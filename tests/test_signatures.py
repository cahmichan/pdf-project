"""Synthetic keys only; verify tampering, trust separation and immutable sources."""
from pathlib import Path
import sys
import pytest
import pymupdf as pdf
import pypdfium2 as pdfium
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.serialization import pkcs12
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'worker'))
from engine import Engine, fingerprint, PDFError


@pytest.fixture
def signing(tmp_path):
    source=tmp_path/'source.pdf'
    doc=pdf.open();page=doc.new_page();page.insert_text((40,60),'Signing fixture 12345')
    doc.set_metadata({'title':'Signed synthetic document'});doc.save(source);doc.close()
    engine=Engine(tmp_path/'data');session=engine.dispatch({'command':'open','args':{'path':str(source)}})
    identity=tmp_path/'synthetic.pfx';password='Synthetic-test-only-123'
    engine.dispatch({'command':'create_identity','args':{'path':str(identity),'name':'Synthetic Test Identity','password':password}})
    return engine,session,source,identity,password


def test_incremental_sign_copy_offline_validation_and_explicit_trust(signing,tmp_path,monkeypatch):
    engine,session,source,identity,password=signing;baseline=fingerprint(source)
    # A network request is a failure even for certificates containing network addresses.
    import socket
    original_connect=socket.socket.connect
    def local_only(connection,address):
        if isinstance(address,tuple) and address[0] in ('127.0.0.1','::1'):return original_connect(connection,address)
        raise AssertionError('External network access forbidden')
    monkeypatch.setattr(socket.socket,'connect',local_only)
    destination=tmp_path/'signed.pdf'
    output=engine.dispatch({'command':'sign_copy','session':session['id'],'revision':session['revision'],
                            'args':{'identity':str(identity),'password':password,'path':str(destination),'reason':'Fixture verification'}})
    signature=output['validation']['signatures'][0]
    assert signature['intact'] and signature['valid'] and not signature['trusted']
    assert signature['coverage']=='ENTIRE_FILE'
    assert destination.read_bytes().startswith(source.read_bytes())
    assert fingerprint(source)==baseline
    assert engine.dispatch({'command':'info','session':session['id']})['revision']==0
    assert password not in (engine.sessions_dir/session['id']/'session.json').read_text()
    with pdfium.PdfDocument(str(destination)) as independent:
        assert '12345' in independent[0].get_textpage().get_text_range()
        assert independent[0].render().width>0
    signed=engine.dispatch({'command':'open','args':{'path':str(destination)}})
    assert signed['signature_fields']
    _,certificate,_=pkcs12.load_key_and_certificates(identity.read_bytes(),password.encode())
    trusted=tmp_path/'explicit.pem'
    public=engine.dispatch({'command':'export_certificate','args':{'identity':str(identity),'password':password,'path':str(trusted)}})
    assert not public['private_key_included']
    assert trusted.read_bytes()==certificate.public_bytes(serialization.Encoding.PEM)
    checked=engine.dispatch({'command':'inspect_signatures','session':signed['id'],'args':{'trust_path':str(trusted)}})
    assert checked['signatures'][0]['trusted'] and checked['offline']
    copied=tmp_path/'exact-copy.pdf'
    engine.dispatch({'command':'export','session':signed['id'],'args':{'path':str(copied)}})
    assert copied.read_bytes()==destination.read_bytes()
    with pytest.raises(PDFError,match='signature'):
        engine.dispatch({'command':'apply','session':signed['id'],'revision':signed['revision'],'args':{'operation':'rotate'}})
    second=tmp_path/'twice-signed.pdf'
    twice=engine.dispatch({'command':'sign_copy','session':signed['id'],'revision':signed['revision'],'args':{'identity':str(identity),'password':password,'path':str(second)}})
    assert len(twice['validation']['signatures'])==2
    assert all(item.get('intact') and item.get('valid') for item in twice['validation']['signatures'])
    changed=tmp_path/'tampered.pdf';changed.write_bytes(destination.read_bytes().replace(b'Signed synthetic document',b'Tamper synthetic document',1))
    assert changed.read_bytes()!=destination.read_bytes()
    altered=engine.dispatch({'command':'open','args':{'path':str(changed)}})
    result=engine.dispatch({'command':'inspect_signatures','session':altered['id']})
    assert not result['signatures'][0]['intact']


def test_identity_and_sign_failures_preserve_outputs(signing,tmp_path):
    engine,session,source,identity,password=signing;before=fingerprint(identity)
    with pytest.raises(ValueError,match='never replaced'):
        engine.dispatch({'command':'create_identity','args':{'path':str(identity),'name':'Other','password':password}})
    assert fingerprint(identity)==before
    for output,secret in ((source,password),(tmp_path/'wrong.pdf','incorrect')):
        with pytest.raises(ValueError):
            engine.dispatch({'command':'sign_copy','session':session['id'],'revision':session['revision'],
                             'args':{'identity':str(identity),'password':secret,'path':str(output)}})
    assert not (tmp_path/'wrong.pdf').exists()
    assert not list(tmp_path.glob('.folio-sign-*'))
