"""Preserve verification evidence alongside a versioned installer."""
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
root=Path(__file__).resolve().parents[1]
status=subprocess.run(['git','status','--porcelain','--untracked-files=no'],cwd=root,capture_output=True,text=True,check=True)
assert not status.stdout.strip(), 'Commit the verified source before saving a milestone checkpoint'
untracked=subprocess.run(['git','ls-files','--others','--exclude-standard','-z'],cwd=root,capture_output=True,text=True,encoding='utf-8',check=True).stdout.split('\0')
untracked=[name for name in untracked if name]
source_roots=('app/','worker/','scripts/','tests/','src-tauri/','docs/','licenses/')
source_extensions={'.py','.rs','.ts','.tsx','.js','.mjs','.css','.html','.json','.toml','.lock','.md','.yaml','.yml','.ps1'}
assert not [name for name in untracked if name.startswith(source_roots) or Path(name).suffix.lower() in source_extensions], 'Commit untracked project source before preserving a checkpoint'
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
forms=evidence/'native-smoke'/'form-drafts-receipt.json'
if forms.exists():
    checked=json.loads(forms.read_text(encoding='utf-8'))
    assert checked['passed'] and hashes['folio.exe']==checked['executable_sha256'] and hashes['pdf-worker.exe']==checked['worker_sha256'], 'Native form receipt is for another build'
assert (release/f'Folio_{version}_x64-setup.exe').is_file(), 'Versioned installer is missing'
camera=evidence/'native-smoke'/'camera-receipt.json'
if camera.exists():
    checked=json.loads(camera.read_text(encoding='utf-8'))
    assert checked['passed'] and hashes['folio.exe']==checked['executable_sha256'] and hashes['pdf-worker.exe']==checked['worker_sha256'], 'Native camera receipt is for another build'
styled=evidence/'native-smoke'/'styled-text-receipt.json'
if styled.exists():
    checked=json.loads(styled.read_text(encoding='utf-8'))
    assert checked['passed'] and hashes['folio.exe']==checked['executable_sha256'] and hashes['pdf-worker.exe']==checked['worker_sha256'], 'Native styled-text receipt is for another build'
checkpoint=subprocess.run(['git','rev-parse','HEAD'],cwd=root,capture_output=True,text=True)
receipt={'version':version,'source_checkpoint':checkpoint.stdout.strip() if checkpoint.returncode==0 else None,'release_binary_sha256':hashes,'native_smoke':native,'untracked_data_files_excluded':len(untracked),'note':'Original receipts copied without modification. Binary hashes were recorded before any subsequent rebuild. Untracked non-source inputs remain untouched and are excluded from the source checkpoint and release evidence.'}
(evidence/'milestone.json').write_text(json.dumps(receipt,indent=2),encoding='utf-8')
print(json.dumps(receipt,indent=2))
