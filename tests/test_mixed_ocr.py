import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'worker'))
import pytest
import pymupdf as pdf
import pypdfium2 as pdfium
from engine import Engine,PDFError,fingerprint


def source_image():
    with pdf.open() as doc:
        page=doc.new_page(width=400,height=250)
        page.insert_text((35,75),'Scanned invoice 24680',fontsize=24)
        page.insert_text((35,145),'Mixed content recognition',fontsize=20)
        return page.get_pixmap(dpi=200).tobytes('png')


@pytest.mark.parametrize('rotation',[0,90,180,270])
def test_mixed_ocr_keeps_digital_text_pixels_geometry_and_repeat_counts(tmp_path,rotation):
    source=tmp_path/'mixed.pdf'
    with pdf.open() as doc:
        page=doc.new_page(width=500,height=700);page.set_cropbox(pdf.Rect(20,30,480,670))
        page.insert_text((35,70),'Digital heading 13579',fontsize=20)
        page.insert_image(pdf.Rect(30,140,430,390),stream=source_image())
        page.insert_text((35,500),'Digital footer remains',fontsize=16);page.set_rotation(rotation);doc.save(source)
    original=fingerprint(source);engine=Engine(tmp_path/'data');opened=engine.open_file({'path':str(source)})
    with pdfium.PdfDocument(opened['path']) as doc:before=doc[0].render(scale=1.2).to_pil().tobytes()
    changed=engine.dispatch({'command':'apply','session':opened['id'],'revision':0,'args':{'operation':'ocr'}})
    with pdf.open(changed['path']) as doc:
        text=doc[0].get_text();assert '24680' in text and text.count('13579')==1 and text.count('Digital footer remains')==1
        assert doc[0].rotation==rotation and list(doc[0].cropbox)==[20,30,480,670]
        hit=doc[0].search_for('24680')[0];assert 30<=hit.x0<hit.x1<=430 and 140<=hit.y0<hit.y1<=390
    with pdfium.PdfDocument(changed['path']) as doc:
        assert doc[0].render(scale=1.2).to_pil().tobytes()==before
        assert '24680' in doc[0].get_textpage().get_text_range()
    again=engine.dispatch({'command':'apply','session':opened['id'],'revision':changed['revision'],'args':{'operation':'ocr'}})
    with pdf.open(again['path']) as doc:
        text=doc[0].get_text();assert text.count('24680')==1 and text.count('13579')==1
    output=tmp_path/'saved.pdf';engine.dispatch({'command':'export','session':opened['id'],'args':{'path':str(output)}})
    with pdfium.PdfDocument(output) as doc:assert '24680' in doc[0].get_textpage().get_text_range()
    undone=engine.dispatch({'command':'undo','session':opened['id'],'revision':again['revision']})
    undone=engine.dispatch({'command':'undo','session':opened['id'],'revision':undone['revision']})
    with pdf.open(undone['path']) as doc:assert '24680' not in doc[0].get_text() and '13579' in doc[0].get_text()
    assert fingerprint(source)==original


def test_legacy_skip_mode_and_large_raster_guard_are_atomic(tmp_path):
    source=tmp_path/'source.pdf'
    with pdf.open() as doc:
        page=doc.new_page(width=500,height=700);page.insert_text((35,70),'Digital heading',fontsize=18);page.insert_image(pdf.Rect(30,140,430,390),stream=source_image());doc.save(source)
    engine=Engine(tmp_path/'data');opened=engine.open_file({'path':str(source)})
    skipped=engine.dispatch({'command':'apply','session':opened['id'],'revision':0,'args':{'operation':'ocr','ocr_mode':'skip_text'}})
    with pdf.open(skipped['path']) as doc:assert '24680' not in doc[0].get_text()
    huge=tmp_path/'huge.pdf'
    with pdf.open() as doc:doc.new_page(width=10000,height=10000);doc.save(huge)
    opened=engine.open_file({'path':str(huge)})
    with pytest.raises(PDFError,match='40 million'):engine.dispatch({'command':'apply','session':opened['id'],'revision':0,'args':{'operation':'ocr'}})
    assert engine.info(engine.session(opened['id']))['revision']==0


def test_hidden_ocr_edits_reject_with_scan_reconstruction_reason(tmp_path):
    source=tmp_path/'scan.pdf'
    with pdf.open() as doc:
        page=doc.new_page(width=400,height=250);page.insert_image(page.rect,stream=source_image());doc.save(source)
    engine=Engine(tmp_path/'data');opened=engine.open_file({'path':str(source)})
    recognized=engine.dispatch({'command':'apply','session':opened['id'],'revision':0,'args':{'operation':'ocr'}})
    block=next(item for item in engine.inspect_page(engine.session(opened['id']),{'page':1})['text_blocks'] if '24680' in item['text'])
    with pytest.raises(PDFError,match='reconstruction'):
        engine.dispatch({'command':'apply','session':opened['id'],'revision':recognized['revision'],'args':{'operation':'edit_text','expected':block['text'],'source_rect':block['raw_rect'],'text':'Invisible replacement'}})
    assert engine.info(engine.session(opened['id']))['revision']==recognized['revision']


def test_batch_ocr_presets_persist_mode_and_resolution(tmp_path):
    source=tmp_path/'source.pdf'
    with pdf.open() as doc:
        page=doc.new_page(width=500,height=700);page.insert_text((35,70),'Digital heading',fontsize=18);page.insert_image(pdf.Rect(30,140,430,390),stream=source_image());doc.save(source)
    engine=Engine(tmp_path/'data')
    for mode in ('missing','skip_text'):
        preset=engine.dispatch({'command':'preset_save','args':{'name':mode,'steps':[{'operation':'ocr','ocr_mode':mode,'dpi':200,'pages':'all'}],'export':'pdf'}})
        result=engine.dispatch({'command':'batch_run','args':{'preset':preset['id'],'paths':[str(source)],'folder':str(tmp_path/mode)}})
        assert result['items'][0]['status']=='done'
        with pdf.open(result['items'][0]['output']) as doc:assert ('24680' in doc[0].get_text())==(mode=='missing')
    with pytest.raises(ValueError,match='OCR mode'):engine.dispatch({'command':'preset_save','args':{'name':'Invalid','steps':[{'operation':'ocr','ocr_mode':'unknown'}]}})
