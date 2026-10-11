from pathlib import Path
from PIL import Image, ImageDraw
import shutil
import hashlib
import urllib.request
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
model=data/'eng.traineddata'
expected='7d4322bd2a7749724879683fc3912cb542f19906c83bcc1a52132556427170b2'
if not model.exists():
    with urllib.request.urlopen('https://raw.githubusercontent.com/tesseract-ocr/tessdata_fast/main/eng.traineddata',timeout=60) as response:
        model.write_bytes(response.read())
if hashlib.sha256(model.read_bytes()).hexdigest()!=expected:
    raise RuntimeError('English OCR model checksum mismatch; review the model before updating the pin.')
if not (data/'LICENSE').exists():
    with urllib.request.urlopen('https://raw.githubusercontent.com/tesseract-ocr/tessdata_fast/main/LICENSE',timeout=60) as response:
        (data/'LICENSE').write_bytes(response.read())
print('Prepared local viewer resources and application icons.')
