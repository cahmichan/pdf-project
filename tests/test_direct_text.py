import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'worker'))
import pytest
import pymupdf as pdf
import pypdfium2 as pdfium
from engine import Engine,PDFError,fingerprint


@pytest.mark.parametrize('rotation',[0,90,180,270])
def test_direct_edit_preserves_font_baseline_neighbors_and_source(tmp_path,rotation):
    source=tmp_path/'original.pdf'
    with pdf.open() as doc:
        page=doc.new_page(width=500,height=700);page.set_cropbox(pdf.Rect(20,30,480,670))
        page.insert_text((40,80),'Original heading',fontname='hebo',fontsize=20,color=(.2,.3,.4))
        page.insert_text((40,230),'Neighbor remains',fontsize=12)
        page.set_rotation(rotation);doc.save(source)
    original=fingerprint(source);engine=Engine(tmp_path/'data');opened=engine.open_file({'path':str(source)})
    block=engine.inspect_page(engine.session(opened['id']),{'page':1})['text_blocks'][0]
    changed=engine.dispatch({'command':'apply','session':opened['id'],'revision':opened['revision'],'args':{'operation':'edit_text','page':1,'expected':block['text'],'source_rect':block['raw_rect'],'text':'Changed heading','font':'original','size':20}})
    with pdf.open(changed['path']) as doc:
        lines=doc[0].get_text('dict')['blocks'];spans=[span for item in lines if item['type']==0 for line in item['lines'] for span in line['spans']]
        edited=next(span for span in spans if 'Changed heading' in span['text'])
        assert edited['font']=='Helvetica-Bold' and abs(edited['origin'][1]-block['origin'][1])<.2
        assert 'Original heading' not in doc[0].get_text() and 'Neighbor remains' in doc[0].get_text()
        assert doc[0].rotation==rotation
    output=tmp_path/'edited.pdf';engine.dispatch({'command':'export','session':opened['id'],'args':{'path':str(output)}})
    with pdfium.PdfDocument(output) as independent:
        page=independent[0];text=page.get_textpage().get_text_range();assert 'Changed heading' in text and 'Original heading' not in text and 'Neighbor remains' in text
        assert page.render().to_pil().getbbox();page.close()
    undone=engine.dispatch({'command':'undo','session':opened['id'],'revision':changed['revision']})
    with pdf.open(undone['path']) as doc:assert 'Original heading' in doc[0].get_text()
    assert fingerprint(source)==original


def test_embedded_source_font_reuse_and_wrapping(tmp_path):
    source=tmp_path/'embedded.pdf'
    with pdf.open() as doc:
        page=doc.new_page(width=500,height=700);page.insert_font(fontname='EmbeddedSource',fontbuffer=pdf.Font('cjk').buffer)
        page.insert_text((40,80),'Original paragraph',fontname='EmbeddedSource',fontsize=18)
        page.insert_text((40,300),'Protected neighbor',fontsize=12);doc.save(source)
    engine=Engine(tmp_path/'data');opened=engine.open_file({'path':str(source)});block=engine.inspect_page(engine.session(opened['id']),{'page':1})['text_blocks'][0]
    text='A longer replacement paragraph with café and Ω characters that wraps naturally across multiple lines in the available page space.'
    changed=engine.dispatch({'command':'apply','session':opened['id'],'revision':0,'args':{'operation':'edit_text','expected':block['text'],'source_rect':block['raw_rect'],'text':text,'font':'original'}})
    with pdf.open(changed['path']) as doc:
        assert 'Ω' in doc[0].get_text() and 'café' in doc[0].get_text() and 'Protected neighbor' in doc[0].get_text()
        assert 'Original paragraph' not in doc[0].get_text()
        assert any('Droid' in span['font'] for item in doc[0].get_text('dict')['blocks'] if item['type']==0 for line in item['lines'] for span in line['spans'])


@pytest.mark.parametrize('rotation',[0,90,180,270])
def test_click_position_adds_visual_text_without_a_user_box(tmp_path,rotation):
    source=tmp_path/'source.pdf'
    with pdf.open() as doc:page=doc.new_page(width=500,height=700);page.set_rotation(rotation);doc.save(source)
    engine=Engine(tmp_path/'data');opened=engine.open_file({'path':str(source)})
    changed=engine.dispatch({'command':'apply','session':opened['id'],'revision':0,'args':{'operation':'insert_text','point':[45,100],'text':'Click and type','size':16,'font':'tiro'}})
    with pdf.open(changed['path']) as doc:
        hits=doc[0].search_for('Click and type');assert hits
        visual=hits[0]*doc[0].rotation_matrix;assert abs(visual.x0-45)<1 and abs(visual.y0-100)<1
    with pdfium.PdfDocument(changed['path']) as doc:assert 'Click and type' in doc[0].get_textpage().get_text_range()


def test_bad_fit_or_stale_selection_rejects_atomically(tmp_path):
    source=tmp_path/'source.pdf'
    with pdf.open() as doc:
        page=doc.new_page(width=300,height=300);page.insert_text((30,60),'Original',fontsize=18);page.insert_text((30,100),'Keep neighbor',fontsize=18);doc.save(source)
    engine=Engine(tmp_path/'data');opened=engine.open_file({'path':str(source)});block=engine.inspect_page(engine.session(opened['id']),{'page':1})['text_blocks'][0]
    for args in ({'expected':'Stale','source_rect':block['raw_rect'],'text':'Bad'},{'expected':block['text'],'source_rect':block['raw_rect'],'text':'Overflow '*300}):
        with pytest.raises(PDFError):engine.dispatch({'command':'apply','session':opened['id'],'revision':0,'args':{'operation':'edit_text',**args}})
        assert engine.info(engine.session(opened['id']))['revision']==0
        assert fingerprint(Path(opened['path']))==fingerprint(source)
