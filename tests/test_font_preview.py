import base64
import hashlib
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'worker'))
import pymupdf as pdf
import pytest
from engine import Engine,PDFError,fingerprint


def fixture(path):
    with pdf.open() as doc:
        page=doc.new_page(width=500,height=700);page.insert_font(fontname='Source',fontbuffer=pdf.Font('cjk').buffer)
        page.insert_text((40,80),'Hello Σ café 中文',fontname='Source',fontsize=20);page.insert_text((40,300),'Keep neighbor',fontsize=12);doc.save(path)


def test_original_ttf_font_bytes_are_read_only_and_not_a_pdfjs_remapped_face(tmp_path):
    source=tmp_path/'font.pdf';fixture(source);original=fingerprint(source);engine=Engine(tmp_path/'data');opened=engine.open_file({'path':str(source)})
    block=engine.inspect_page(engine.session(opened['id']),{'page':1})['text_blocks'][0]
    result=engine.dispatch({'command':'preview_fonts','session':opened['id'],'revision':0,'args':{'page':1,'fonts':[block['font']]}})['fonts'][0]
    raw=base64.b64decode(result['data']);assert result['status']=='embedded' and result['format']=='ttf'
    assert raw==pdf.Font('cjk').buffer and hashlib.sha256(raw).hexdigest()==result['sha256']
    assert engine.info(engine.session(opened['id']))['revision']==0 and fingerprint(source)==original
    with pytest.raises(PDFError,match='document changed'):
        engine.dispatch({'command':'preview_fonts','session':opened['id'],'revision':1,'args':{'page':1,'fonts':[block['font']]}})


def test_missing_fonts_and_invalid_page_reject_and_base14_reports_substitute(tmp_path):
    source=tmp_path/'base.pdf'
    with pdf.open() as doc:
        doc.new_page().insert_text((40,80),'Ordinary text');doc.save(source)
    engine=Engine(tmp_path/'data');opened=engine.open_file({'path':str(source)});request={'command':'preview_fonts','session':opened['id'],'revision':0}
    result=engine.dispatch({**request,'args':{'fonts':['Helvetica']}})['fonts'][0]
    assert result['status']=='substitute' and 'data' not in result
    for args in ({'fonts':['Unknown']},{'fonts':[]},{'fonts':['Helvetica'],'page':2}):
        with pytest.raises(PDFError):engine.dispatch({**request,'args':args})
