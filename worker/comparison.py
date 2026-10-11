"""Local, position-by-position text and rendered-pixel comparison."""
import base64
import difflib
import html
import io
import json
from pathlib import Path
import pymupdf as pdf
from PIL import Image, ImageChops


def compare(first: Path, second: Path, folder: Path, progress) -> dict:
    folder.mkdir(parents=True,exist_ok=True)
    records=[]; sections=[]
    with pdf.open(first) as left, pdf.open(second) as right:
        if right.needs_pass:
            raise ValueError('Unlock the second PDF before comparing it.')
        for n in range(max(len(left),len(right))):
            progress(n/max(len(left),len(right)),f'Comparing page {n+1}')
            a=left[n] if n<len(left) else None; b=right[n] if n<len(right) else None
            text_a=a.get_text(sort=True) if a else '';text_b=b.get_text(sort=True) if b else ''
            text_diff='\n'.join(difflib.unified_diff(text_a.splitlines(),text_b.splitlines(),fromfile='Current',tofile='Other',lineterm=''))
            def render(page):
                if page is None: return Image.new('RGB',(1,1),'white')
                # Bound memory for poster-size pages while keeping a shared physical scale.
                scale=min(1,1600/max((a.rect.width if a else 0),(a.rect.height if a else 0),(b.rect.width if b else 0),(b.rect.height if b else 0)))
                pix=page.get_pixmap(matrix=pdf.Matrix(scale,scale),colorspace=pdf.csRGB,alpha=False)
                return Image.frombytes('RGB',(pix.width,pix.height),pix.samples)
            im_a=render(a);im_b=render(b)
            size=(max(im_a.width,im_b.width),max(im_a.height,im_b.height))
            canvas_a=Image.new('RGB',size,'white');canvas_a.paste(im_a,(0,0))
            canvas_b=Image.new('RGB',size,'white');canvas_b.paste(im_b,(0,0))
            difference=ImageChops.difference(canvas_a,canvas_b)
            channels=difference.split();mask=ImageChops.lighter(ImageChops.lighter(channels[0],channels[1]),channels[2]).point(lambda value:255 if value>12 else 0)
            changed=sum(mask.histogram()[1:]); ratio=changed/(size[0]*size[1])
            dimensions_changed=a is None or b is None or tuple(a.rect)!=tuple(b.rect)
            flagged=bool(text_diff or changed or dimensions_changed)
            diff_path=folder/f'page-{n+1}.png'
            if flagged:
                overlay=Image.blend(canvas_a,Image.new('RGB',size,'white'),.6)
                overlay.paste((232,45,119),mask=mask);overlay.save(diff_path)
                stream=io.BytesIO();overlay.save(stream,format='PNG')
                encoded=base64.b64encode(stream.getvalue()).decode('ascii')
                sections.append(f'<section><h2>Page {n+1}</h2><p>{ratio:.2%} rendered pixels changed; page dimensions changed: {dimensions_changed}</p><pre>{html.escape(text_diff)}</pre><img alt="Differences marked in pink" src="data:image/png;base64,{encoded}"></section>')
            records.append({'page':n+1,'changed':flagged,'pixel_ratio':ratio,'dimensions_changed':dimensions_changed,'text_diff':text_diff,'image':str(diff_path) if flagged else None})
        result={'left_pages':len(left),'right_pages':len(right),'changed_pages':sum(item['changed'] for item in records),'pages':records,
                'report':str(folder/'report.html'),'note':'Pages are matched by position. Pixel comparison uses up to 72 DPI with a color threshold; it is not a semantic or compliance check.'}
    document='<!doctype html><meta charset="utf-8"><title>Folio PDF comparison</title><style>body{font:16px system-ui;margin:40px;color:#24334d}img{max-width:100%;border:1px solid #ddd}pre{white-space:pre-wrap;background:#f3f5fa;padding:20px}section{margin:40px 0;page-break-before:always}</style>'
    document+=f'<h1>Folio PDF comparison</h1><p>{result["changed_pages"]} changed pages. Current: {result["left_pages"]} pages. Other: {result["right_pages"]} pages.</p><p>{html.escape(result["note"])}</p>'+''.join(sections)
    (folder/'report.html').write_text(document,encoding='utf-8')
    (folder/'result.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    return result
