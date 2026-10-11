"""Extract a free project-local LibreOffice runtime without application installation."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import urllib.request
import zipfile

root=Path(__file__).resolve().parents[1]
version='26.8.1'
url=f'https://download.documentfoundation.org/libreoffice/stable/{version}/win/x86_64/LibreOffice_{version}_Win_x86-64.msi'
expected='c6298b10cfa1748bcbedad94c62ce771e240e5021bfd6d7a967cd571b04b5312'
downloads=root/'tools'/'downloads';downloads.mkdir(parents=True,exist_ok=True)
installer=downloads/f'LibreOffice_{version}_Win_x86-64.msi'
if not installer.exists():
    temporary=installer.with_suffix('.partial')
    # Windows curl uses system certificate trust for mirror downloads.
    curl=Path(os.environ['SystemRoot'])/'System32'/'curl.exe'
    subprocess.run([str(curl),'--fail','--location','--connect-timeout','30','--max-time','600','--output',str(temporary),url],check=True)
    temporary.replace(installer)
with installer.open('rb') as stream:
    digest=hashlib.file_digest(stream,'sha256').hexdigest()
if digest!=expected:
    raise RuntimeError('LibreOffice checksum mismatch. Do not execute this package.')
target=root/'tools'/'LibreOffice';target.mkdir(parents=True,exist_ok=True)
logs=root/'artifacts'/'office';logs.mkdir(parents=True,exist_ok=True)
runtime=target/'SourceDir'/'LibreOffice'/'program'/'soffice.com'
if not runtime.exists():
    extractor=root/'tools'/'lessmsi'/'lessmsi.exe'
    if not extractor.exists():
        archive=downloads/'lessmsi-v2.12.9.zip'
        with urllib.request.urlopen('https://github.com/activescott/lessmsi/releases/download/v2.12.9/lessmsi-v2.12.9.zip',timeout=30) as response:
            archive.write_bytes(response.read())
        if hashlib.sha256(archive.read_bytes()).hexdigest()!='5b4e187e74b184ad3a63ccf06c3d17dae2b8c4b6c298a996dbd51a9f6db29d21':
            raise RuntimeError('lessmsi checksum mismatch.')
        with zipfile.ZipFile(archive) as package:package.extractall(extractor.parent)
    with (logs/'extraction.log').open('w',encoding='utf-8') as output:
        result=subprocess.run([str(extractor),'x',str(installer),str(target)+'\\'],stdout=output,stderr=subprocess.STDOUT,timeout=300,creationflags=subprocess.CREATE_NO_WINDOW)
    if result.returncode!=0 or not runtime.exists():
        raise RuntimeError(f'LibreOffice extraction failed ({result.returncode}); see {logs / "extraction.log"}')
receipt={'version':version,'url':url,'sha256':digest,'runtime':str(runtime),'method':'lessmsi file extraction; no Windows application registration'}
(logs/'runtime.json').write_text(json.dumps(receipt,indent=2),encoding='utf-8')
app_data=Path(os.environ['APPDATA'])/'personal.folio.pdf';app_data.mkdir(parents=True,exist_ok=True)
settings=app_data/'settings.json'
configuration=json.loads(settings.read_text(encoding='utf-8')) if settings.exists() else {}
configuration['office_runtime']=str(runtime)
temporary=settings.with_suffix('.pending.json');temporary.write_text(json.dumps(configuration,indent=2),encoding='utf-8');temporary.replace(settings)
print(json.dumps(receipt,indent=2))
