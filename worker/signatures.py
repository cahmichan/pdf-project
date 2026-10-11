"""Local certificate signing and explicit-trust offline inspection.

Signing exports an incremental copy; it must never run through commit's rewrite.
Passwords and private key material are not stored in sessions or job receipts.
"""
from datetime import datetime, timedelta, timezone
import logging
import os
from pathlib import Path
import uuid

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.serialization import pkcs12
from cryptography.x509.oid import NameOID
from pyhanko.keys import load_certs_from_pemder
from pyhanko.pdf_utils.incremental_writer import IncrementalPdfFileWriter
from pyhanko.pdf_utils.reader import PdfFileReader
from pyhanko.sign import fields, signers
from pyhanko.sign.validation import validate_pdf_signature
from pyhanko_certvalidator import ValidationContext

# Trust failures are returned in validation details; avoid redundant warning tracebacks.
logging.getLogger('pyhanko.sign.validation.generic_cms').setLevel(logging.ERROR)


def inspect_signatures(path: Path, trust_path: str | None = None) -> dict:
    roots = list(load_certs_from_pemder([trust_path])) if trust_path else []
    context = ValidationContext(trust_roots=roots, allow_fetching=False,
                                revocation_mode='soft-fail')
    results = []
    with path.open('rb') as stream:
        reader = PdfFileReader(stream)
        signatures = reader.embedded_signatures
        if len(signatures) > 100:
            raise ValueError('Inspect up to 100 signatures per PDF.')
        for signature in signatures:
            try:
                status = validate_pdf_signature(signature, signer_validation_context=context)
                results.append({'field': signature.field_name,
                                'signer': signature.signer_cert.subject.human_friendly,
                                'intact': bool(status.intact), 'valid': bool(status.valid),
                                'trusted': bool(status.trusted),
                                'coverage': status.coverage.name if status.coverage is not None else 'UNKNOWN',
                                'modification': status.modification_level.name if status.modification_level is not None else 'UNKNOWN',
                                'docmdp_ok': bool(status.docmdp_ok),
                                'details': status.pretty_print_details()})
            except Exception as error:
                results.append({'field': signature.field_name, 'error': str(error)})
    return {'signatures': results, 'offline': True, 'explicit_trust_roots': len(roots),
            'note': 'No network checks. Revocation and trusted timestamp assurance are not established by this inspection.'}


def create_identity(args: dict) -> dict:
    name = str(args.get('name', '')).strip()
    password = str(args.get('password', ''))
    if not 1 <= len(name) <= 100:
        raise ValueError('Enter a personal certificate name (up to 100 characters).')
    if len(password) < 8:
        raise ValueError('Use at least 8 characters to protect the private key.')
    destination = Path(args['path']).resolve()
    if destination.suffix.lower() not in ('.pfx', '.p12'):
        raise ValueError('Save the identity as a .pfx or .p12 file.')
    if destination.exists():
        raise ValueError('Choose a new identity file name; existing private keys are never replaced.')
    destination.parent.mkdir(parents=True, exist_ok=True)
    key = rsa.generate_private_key(public_exponent=65537, key_size=3072)
    subject = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, name)])
    now = datetime.now(timezone.utc)
    certificate = (x509.CertificateBuilder().subject_name(subject).issuer_name(subject)
                   .public_key(key.public_key()).serial_number(x509.random_serial_number())
                   .not_valid_before(now-timedelta(minutes=5)).not_valid_after(now+timedelta(days=1095))
                   .add_extension(x509.BasicConstraints(ca=False, path_length=None), critical=True)
                   .add_extension(x509.KeyUsage(digital_signature=True, content_commitment=True,
                                                key_encipherment=False, data_encipherment=False,
                                                key_agreement=False, key_cert_sign=False, crl_sign=False,
                                                encipher_only=None, decipher_only=None), critical=True)
                   .sign(key, hashes.SHA256()))
    data = pkcs12.serialize_key_and_certificates(name.encode('utf-8'), key, certificate, None,
                                                serialization.BestAvailableEncryption(password.encode('utf-8')))
    # Exclusive creation prevents replacing another identity even if it appears mid-operation.
    created = False
    try:
        with destination.open('xb') as stream:
            created = True
            stream.write(data)
    except Exception:
        if created: destination.unlink(missing_ok=True)
        raise
    return {'path': str(destination), 'self_signed': True,
            'fingerprint': certificate.fingerprint(hashes.SHA256()).hex(),
            'note': 'Personal self-signed identity. It is not automatically trusted by other readers.'}


def sign_copy(source: Path, original: str | None, args: dict) -> dict:
    destination = Path(args['path']).resolve()
    identity = Path(args['identity']).resolve()
    if destination.suffix.lower() != '.pdf':
        raise ValueError('Choose a PDF output file.')
    if destination == source.resolve() or destination == identity or (original and destination == Path(original).resolve()):
        raise ValueError('Choose a separate signed output to preserve the source and identity.')
    if destination.exists() and not args.get('overwrite'):
        raise ValueError('The signed output already exists. Confirm replacement or use a new name.')
    destination.parent.mkdir(parents=True, exist_ok=True)
    password = str(args.get('password', '')).encode('utf-8')
    try:
        signer = signers.SimpleSigner.load_pkcs12_data(identity.read_bytes(), other_certs=[], passphrase=password or None)
    except Exception:
        raise ValueError('Cannot open this signing identity. Check its password and PKCS#12 format.') from None
    temporary = destination.parent / f'.folio-sign-{uuid.uuid4().hex}.pdf'
    field_name = f'FolioSignature_{uuid.uuid4().hex[:12]}'
    try:
        with source.open('rb') as input_stream, temporary.open('wb') as output:
            writer = IncrementalPdfFileWriter(input_stream)
            signers.sign_pdf(writer, signers.PdfSignatureMetadata(field_name=field_name,
                             reason=str(args.get('reason', ''))[:500], md_algorithm='sha256'), signer=signer,
                             new_field_spec=fields.SigFieldSpec(field_name), output=output)
        # Verify integrity and the CMS signature before publishing the output.
        checked = inspect_signatures(temporary)
        added = next((s for s in checked['signatures'] if s['field'] == field_name), None)
        if not added or not added.get('intact') or not added.get('valid'):
            raise ValueError('The generated signature failed integrity verification.')
        os.replace(temporary, destination)
        return {'path': str(destination), 'bytes': destination.stat().st_size,
                'field': field_name, 'validation': checked}
    finally:
        temporary.unlink(missing_ok=True)


def export_certificate(args: dict) -> dict:
    identity = Path(args['identity']).resolve()
    destination = Path(args['path']).resolve()
    if destination == identity or destination.suffix.lower() not in ('.pem', '.cer', '.crt'):
        raise ValueError('Choose a separate .pem, .cer or .crt public certificate file.')
    if destination.exists():
        raise ValueError('Choose a new public certificate file name.')
    try:
        _, certificate, _ = pkcs12.load_key_and_certificates(identity.read_bytes(), str(args.get('password', '')).encode('utf-8') or None)
    except Exception:
        raise ValueError('Cannot open this signing identity. Check its password and PKCS#12 format.') from None
    if certificate is None:
        raise ValueError('This identity contains no certificate.')
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open('xb') as stream:
        stream.write(certificate.public_bytes(serialization.Encoding.PEM))
    return {'path': str(destination), 'private_key_included': False,
            'fingerprint': certificate.fingerprint(hashes.SHA256()).hex()}
