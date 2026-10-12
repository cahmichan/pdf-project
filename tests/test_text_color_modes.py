import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'worker'))
import pymupdf as pdf
import pypdfium2 as pdfium
import pytest
from engine import Engine,PDFError,fingerprint


@pytest.mark.parametrize('mode,color,expected',[('uniform','#000000',[0,0]),('uniform','#2244aa',[0x2244aa,0x2244aa]),('original','#2244aa',[0,0xcc0000]),('auto','#000000',[0,0xcc0000])])
def test_explicit_paragraph_color_modes_keep_fonts_and_save_reopen(tmp_path,mode,color,expected):
    source=tmp_path/'source.pdf'
    with pdf.open() as doc:
        page=doc.new_page(width=500,height=700);page.insert_text((40,80),'Plain ',fontsize=14)
        page.insert_text((76,80),'bold',fontname='hebo',fontsize=18,color=(.8,0,0));page.insert_text((40,300),'Keep neighbor',fontsize=12);doc.save(source)
    original=fingerprint(source);engine=Engine(tmp_path/'data');opened=engine.open_file({'path':str(source)})
    block=engine.inspect_page(engine.session(opened['id']),{'page':1})['text_blocks'][0]
    changed=engine.dispatch({'command':'apply','session':opened['id'],'revision':0,'args':{'operation':'edit_text','text':block['text'],'expected':block['text'],'source_rect':block['raw_rect'],'font':'original','color':color,'color_mode':mode}})
    output=tmp_path/'output.pdf';engine.dispatch({'command':'export','session':opened['id'],'args':{'path':str(output)}})
    with pdf.open(output) as doc:
        spans=[s for b in doc[0].get_text('dict')['blocks'] if b['type']==0 for l in b['lines'] for s in l['spans']]
        plain=next(s for s in spans if 'Plain' in s['text']);bold=next(s for s in spans if 'bold' in s['text'])
        assert [plain['color'],bold['color']]==expected
        assert plain['font']=='Helvetica' and bold['font']=='Helvetica-Bold' and abs(bold['size']-18)<.1
    with pdfium.PdfDocument(output) as doc:
        assert 'Keep neighbor' in doc[0].get_textpage().get_text_range() and doc[0].render().to_pil().getbbox()
    engine.dispatch({'command':'undo','session':opened['id'],'revision':changed['revision']})
    assert fingerprint(source)==original


def test_invalid_color_mode_rejects_without_revision(tmp_path):
    source=tmp_path/'source.pdf'
    with pdf.open() as doc:
        doc.new_page().insert_text((40,80),'Original');doc.save(source)
    engine=Engine(tmp_path/'data');opened=engine.open_file({'path':str(source)})
    with pytest.raises(PDFError,match='paragraph color'):
        engine.dispatch({'command':'apply','session':opened['id'],'revision':0,'args':{'operation':'edit_text','color_mode':'unsupported'}})
    assert engine.info(engine.session(opened['id']))['revision']==0
