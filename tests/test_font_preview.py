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


def test_missing_fonts_and_invalid_page_reject_and_base14_reports_compatible(tmp_path):
    source=tmp_path/'base.pdf'
    with pdf.open() as doc:
        doc.new_page().insert_text((40,80),'Ordinary text');doc.save(source)
    engine=Engine(tmp_path/'data');opened=engine.open_file({'path':str(source)});request={'command':'preview_fonts','session':opened['id'],'revision':0}
    result=engine.dispatch({**request,'args':{'fonts':['Helvetica']}})['fonts'][0]
    assert result['status']=='compatible' and result['format']=='otf' and base64.b64decode(result['data'])[:4]==b'OTTO'
    for args in ({'fonts':['Unknown']},{'fonts':[]},{'fonts':['Helvetica'],'page':2}):
        with pytest.raises(PDFError):engine.dispatch({**request,'args':args})


@pytest.mark.parametrize('name',['helv','hebo','heit','hebi','tiro','tibo','tiit','tibi','cour','cobo','coit','cobi','symb','zadb'])
def test_cff_wrapping_preserves_unicode_glyph_outlines_and_advances(name):
    import io
    from cff_preview import convert
    from fontTools.cffLib import CFFFontSet
    from fontTools.ttLib import TTFont
    from fontTools.pens.recordingPen import RecordingPen
    original=pdf.Font(name);raw=original.buffer;converted=convert(raw)
    assert convert(raw)==converted
    source=CFFFontSet();source.decompile(io.BytesIO(raw),None)
    with TTFont(io.BytesIO(converted)) as loaded:
        for glyph in source.topDictIndex[0].charset:
            before=RecordingPen();after=RecordingPen();source.topDictIndex[0].CharStrings[glyph].draw(before);loaded['CFF '].cff.topDictIndex[0].CharStrings[glyph].draw(after)
            assert before.value==after.value
        check=pdf.Font(fontbuffer=converted)
        for code in loaded.getBestCmap():
            assert abs(original.glyph_advance(code)-check.glyph_advance(code))<.001


def cff_fixture(path):
    with pdf.open() as doc:
        page=doc.new_page(width=500,height=700);page.insert_font(fontname='Source',fontbuffer=pdf.Font('helv').buffer)
        page.insert_text((40,80),'CFF café Σ',fontname='Source',fontsize=20);page.insert_text((40,300),'Keep neighbor',fontsize=12);doc.save(path)


def test_embedded_cff_has_original_provenance_and_verified_opentype_output(tmp_path):
    source=tmp_path/'cff.pdf';cff_fixture(source);engine=Engine(tmp_path/'data');opened=engine.open_file({'path':str(source)})
    block=engine.inspect_page(engine.session(opened['id']),{'page':1})['text_blocks'][0]
    font=engine.dispatch({'command':'preview_fonts','session':opened['id'],'revision':0,'args':{'fonts':[block['font']]}})['fonts'][0]
    assert font['status']=='embedded' and font['source_format'] in ('cff','cid') and font['format']=='otf'
    assert font['source_sha256']==hashlib.sha256(pdf.Font('helv').buffer).hexdigest()
