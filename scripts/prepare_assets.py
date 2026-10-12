from pathlib import Path
from PIL import Image, ImageDraw
import shutil
import hashlib
import urllib.request
import json
root=Path(__file__).resolve().parents[1]
icons=root/'src-tauri'/'icons';icons.mkdir(parents=True,exist_ok=True)
image=Image.new('RGBA',(256,256),(52,88,216,255));draw=ImageDraw.Draw(image)
draw.rounded_rectangle((66,40,190,215),radius=13,fill='white')
for y in (96,124,152,180):draw.rounded_rectangle((87,y,168,y+8),radius=4,fill=(52,88,216))
image.save(icons/'icon.ico',sizes=[(16,16),(32,32),(48,48),(64,64),(128,128),(256,256)])
image.save(icons/'icon.png')
for name in ('cmaps','standard_fonts','wasm'):
    source=root/'node_modules'/'pdfjs-dist'/name
    if source.is_dir():shutil.copytree(source,root/'public'/'pdfjs'/name,dirs_exist_ok=True)
data=root/'tools'/'tessdata';data.mkdir(parents=True,exist_ok=True)
manifest=json.loads((root/'worker'/'ocr-models.json').read_text(encoding='utf-8'))
for item in manifest['models']:
    model=data/(item['language']+'.traineddata')
    if not model.exists():
        url=f"https://raw.githubusercontent.com/tesseract-ocr/tessdata_fast/{manifest['commit']}/{item['language']}.traineddata"
        with urllib.request.urlopen(url,timeout=60) as response:content=response.read()
        if len(content)!=item['bytes'] or hashlib.sha256(content).hexdigest()!=item['sha256']:
            raise RuntimeError('Downloaded OCR model checksum mismatch: '+item['language'])
        temporary=model.with_suffix('.pending');temporary.write_bytes(content);temporary.replace(model)
    if model.stat().st_size!=item['bytes'] or hashlib.sha256(model.read_bytes()).hexdigest()!=item['sha256']:
        raise RuntimeError('OCR model checksum mismatch: '+item['language'])
if not (data/'LICENSE').exists():
    with urllib.request.urlopen(f"https://raw.githubusercontent.com/tesseract-ocr/tessdata_fast/{manifest['commit']}/LICENSE",timeout=60) as response:
        (data/'LICENSE').write_bytes(response.read())
(data/'models.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
print('Prepared local viewer resources and application icons.')
