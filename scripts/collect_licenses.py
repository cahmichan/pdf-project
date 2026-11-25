"""Keep exact installed dependency notices with each local release."""
import importlib.metadata as metadata
import json
import shutil
from pathlib import Path
root=Path(__file__).resolve().parents[1]
folder=root/'licenses';folder.mkdir(exist_ok=True)
inventory=[]
from fontTools import agl
for label in ('_aglText','_aglfnText'):
    notice=[]
    for line in getattr(agl,label).splitlines():
        if line and not line.startswith('#'):break
        notice.append(line)
    destination=folder/'python'/'fonttools'/(label.strip('_')+'-Adobe-NOTICE.txt')
    destination.parent.mkdir(parents=True,exist_ok=True);destination.write_text('\n'.join(notice)+'\n',encoding='utf-8')
for package in metadata.distributions():
    name=package.metadata['Name'];version=package.version
    inventory.append({'ecosystem':'python','name':name,'version':version,'license':package.metadata.get('License-Expression') or package.metadata.get('License') or 'See package notices'})
    for entry in package.files or []:
        if any(word in entry.name.lower() for word in ('license','copying','notice')):
            source=Path(package.locate_file(entry))
            if source.is_file():
                target=folder/'python'/name/str(entry)
                target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(source,target)
for manifest in (root/'node_modules').glob('**/package.json'):
    try:package=json.loads(manifest.read_text(encoding='utf-8'))
    except (OSError,ValueError):continue
    if not package.get('name') or not package.get('version'):continue
    inventory.append({'ecosystem':'npm','name':package['name'],'version':package['version'],'license':package.get('license','See package notices')})
    for source in manifest.parent.iterdir():
        if source.is_file() and any(word in source.name.lower() for word in ('license','copying','notice')):
            target=folder/'npm'/package['name'].replace('/','_')/source.name
            target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(source,target)
(folder/'inventory.json').write_text(json.dumps(inventory,indent=2),encoding='utf-8')
for package in metadata.distributions():
    if package.metadata['Name'].lower()=='pymupdf':
        for entry in package.files or []:
            if entry.name=='COPYING':shutil.copyfile(package.locate_file(entry),root/'LICENSE')
print(f'Collected license metadata for {len(inventory)} installed packages.')
ocr=root/'tools'/'tessdata'/'LICENSE'
if ocr.exists():
    (folder/'tesseract-data').mkdir(exist_ok=True)
    shutil.copyfile(ocr,folder/'tesseract-data'/'LICENSE')

ocr_models=root/"tools"/"tessdata"/"models.json"
if ocr_models.exists():shutil.copyfile(ocr_models,folder/"tesseract-data"/"models.json")
