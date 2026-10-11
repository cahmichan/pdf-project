"""Preserve verification evidence alongside a versioned installer."""
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
root=Path(__file__).resolve().parents[1]
version=json.loads((root/'package.json').read_text(encoding='utf-8'))['version']
release=root/'artifacts'/'releases'/version
evidence=release/'verification';evidence.mkdir(parents=True,exist_ok=True)
for source in ('native-smoke','packaged-smoke','benchmark','ui'):
    for path in (root/'artifacts'/source).glob('*'):
        if path.suffix in ('.json','.png'):
            destination=evidence/source/path.name;destination.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(path,destination)
if (root/'artifacts'/'ui-test-results.json').exists():shutil.copyfile(root/'artifacts'/'ui-test-results.json',evidence/'ui-test-results.json')
native=json.loads((evidence/'native-smoke'/'receipt.json').read_text(encoding='utf-8'))
assert native['passed']
hashes={}
for name in ('folio.exe','pdf-worker.exe'):
    path=root/'src-tauri'/'target'/'release'/name
    with path.open('rb') as stream:hashes[name]=hashlib.file_digest(stream,'sha256').hexdigest()
assert hashes['folio.exe']==native['executable_sha256'], 'Native receipt is for another application build'
assert hashes['pdf-worker.exe']==native['worker_sha256'], 'Native receipt is for another worker build'
assert (release/f'Folio_{version}_x64-setup.exe').is_file(), 'Versioned installer is missing'
checkpoint=subprocess.run(['git','rev-parse','HEAD'],cwd=root,capture_output=True,text=True)
receipt={'version':version,'source_checkpoint':checkpoint.stdout.strip() if checkpoint.returncode==0 else None,'release_binary_sha256':hashes,'native_smoke':native,'note':'Original receipts copied without modification. Binary hashes were recorded before any subsequent rebuild.'}
(evidence/'milestone.json').write_text(json.dumps(receipt,indent=2),encoding='utf-8')
print(json.dumps(receipt,indent=2))
