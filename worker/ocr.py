"""Persistent OCR that preserves visible content and existing searchable words."""
import io
import math
import pymupdf as pdf
from PIL import Image,ImageDraw


def add_missing_text(page,language,data,dpi,mode='missing'):
    from engine import PDFError
    if mode not in ('missing','skip_text'):raise PDFError('Choose missing-text OCR or skip existing text pages.')
    existing=[pdf.Rect(word[:4]) for word in page.get_text('words')]
    if existing and (mode=='skip_text' or not page.get_image_info()):return {'skipped':True,'words_added':0}
    rotation=page.rotation;page.set_rotation(0)
    try:
        # Re-extract after derotation, matching the rendered page coordinates.
        existing=[pdf.Rect(word[:4]) for word in page.get_text('words')]
        if math.ceil(page.rect.width*dpi/72)*math.ceil(page.rect.height*dpi/72)>40_000_000:
            raise PDFError('OCR rendering exceeds 40 million pixels. Reduce the DPI or process smaller pages.')
        raster=page.get_pixmap(dpi=dpi,colorspace=pdf.csRGB,alpha=False)
        if raster.width*raster.height>40_000_000:raise PDFError('OCR rendering exceeds 40 million pixels. Reduce the DPI or process smaller pages.')
        if existing:
            image=Image.frombytes('RGB',(raster.width,raster.height),raster.samples)
            draw=ImageDraw.Draw(image);sx=raster.width/page.rect.width;sy=raster.height/page.rect.height
            for rect in existing:
                rect=pdf.Rect(rect.x0-2,rect.y0-2,rect.x1+2,rect.y1+2)&page.rect
                draw.rectangle((math.floor(rect.x0*sx),math.floor(rect.y0*sy),math.ceil(rect.x1*sx),math.ceil(rect.y1*sy)),fill='white')
            encoded=io.BytesIO();image.save(encoded,format='PNG');raster=pdf.Pixmap(encoded.getvalue())
            raster.set_dpi(dpi,dpi)
        with pdf.open('pdf',raster.pdfocr_tobytes(language=language,tessdata=str(data))) as recognized:
            target=recognized[0];words=target.get_text('words');mapping=target.rect.torect(page.rect)
            kept=[]
            for word in words:
                mapped=pdf.Rect(word[:4])*mapping
                duplicate=any(mapped.intersects(old) and (mapped&old).get_area()>=min(mapped.get_area(),old.get_area())*.2 for old in existing)
                if duplicate:target.add_redact_annot(pdf.Rect(word[:4]),fill=False)
                else:kept.append(word)
            if len(kept)!=len(words):target.apply_redactions(images=0,graphics=0,text=0)
            if not kept:return {'skipped':False,'words_added':0}
            for item in target.get_images():target.delete_image(item[0])
            page.show_pdf_page(page.rect,recognized,0)
            return {'skipped':False,'words_added':len(kept)}
    finally:
        page.set_rotation(rotation)
