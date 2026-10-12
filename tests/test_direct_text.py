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


@pytest.mark.parametrize('rotation',[0,90,180,270])
def test_mixed_style_word_edit_preserves_bold_color_font_and_relative_sizes(tmp_path,rotation):
    source=tmp_path/'mixed.pdf'
    with pdf.open() as doc:
        page=doc.new_page(width=500,height=700)
        x=40
        for text,font,size,color in [('Total: ','helv',14,(0,0,0)),('$100','hebo',18,(.8,0,0)),(' paid','tiit',14,(0,.3,0))]:
            page.insert_text((x,80),text,fontname=font,fontsize=size,color=color);x+=pdf.get_text_length(text,fontname=font,fontsize=size)
        page.insert_text((40,300),'Unchanged neighbor',fontsize=12);page.set_rotation(rotation);doc.save(source)
    original=fingerprint(source);engine=Engine(tmp_path/'data');opened=engine.open_file({'path':str(source)})
    block=engine.inspect_page(engine.session(opened['id']),{'page':1})['text_blocks'][0]
    assert block['mixed_styles'] and block['text']=='Total: $100 paid'
    changed=engine.dispatch({'command':'apply','session':opened['id'],'revision':0,'args':{'operation':'edit_text','expected':block['text'],'source_rect':block['raw_rect'],'text':'Total: $125 paid','font':'original','size':14,'color':block['color']}})
    with pdf.open(changed['path']) as doc:
        spans=[span for item in doc[0].get_text('dict')['blocks'] if item['type']==0 for line in item['lines'] for span in line['spans']]
        amount=next(span for span in spans if '$125' in span['text'])
        assert amount['font']=='Helvetica-Bold' and abs(amount['size']-18)<.1 and amount['color']&0xff0000
        paid=next(span for span in spans if 'paid' in span['text'])
        assert paid['font']=='Times-Italic' and paid['color']&0x00ff00
        assert 'Unchanged neighbor' in doc[0].get_text() and '$100' not in doc[0].get_text()
    with pdfium.PdfDocument(changed['path']) as doc:
        assert '$125' in doc[0].get_textpage().get_text_range() and '$100' not in doc[0].get_textpage().get_text_range()
        assert doc[0].render().to_pil().getbbox()
    assert fingerprint(source)==original


def test_styled_insertions_wrap_and_failed_fit_preserves_the_revision(tmp_path):
    source=tmp_path/'source.pdf'
    with pdf.open() as doc:
        page=doc.new_page(width=300,height=400)
        page.insert_text((30,60),'Plain ',fontsize=14)
        page.insert_text((65,60),'bold',fontname='hebo',fontsize=14)
        page.insert_text((30,220),'Keep neighbor',fontsize=12);doc.save(source)
    engine=Engine(tmp_path/'data');opened=engine.open_file({'path':str(source)});block=engine.inspect_page(engine.session(opened['id']),{'page':1})['text_blocks'][0]
    base={'operation':'edit_text','expected':block['text'],'source_rect':block['raw_rect'],'font':'original'}
    with pytest.raises(PDFError):engine.dispatch({'command':'apply','session':opened['id'],'revision':0,'args':{**base,'text':'Plain '+'bold '*200}})
    assert engine.info(engine.session(opened['id']))['revision']==0
    changed=engine.dispatch({'command':'apply','session':opened['id'],'revision':0,'args':{**base,'text':'Plain bold emphasis repeated enough to wrap onto a second line'}})
    with pdf.open(changed['path']) as doc:
        assert 'second line' in doc[0].get_text() and 'Keep neighbor' in doc[0].get_text()
        assert any(span['font']=='Helvetica-Bold' and 'emphasis' in span['text'] for item in doc[0].get_text('dict')['blocks'] if item['type']==0 for line in item['lines'] for span in line['spans'])


def test_original_style_mode_scales_relative_sizes_and_applies_explicit_color(tmp_path):
    source=tmp_path/'styles.pdf'
    with pdf.open() as doc:
        page=doc.new_page(width=500,height=700);page.insert_text((40,80),'Normal ',fontsize=14)
        page.insert_text((90,80),'bold',fontname='hebo',fontsize=18,color=(.8,0,0));doc.save(source)
    engine=Engine(tmp_path/'data');opened=engine.open_file({'path':str(source)});block=engine.inspect_page(engine.session(opened['id']),{'page':1})['text_blocks'][0]
    changed=engine.dispatch({'command':'apply','session':opened['id'],'revision':0,'args':{'operation':'edit_text','expected':block['text'],'source_rect':block['raw_rect'],'text':'Normal bold changed','font':'original','size':28,'color':'#2244aa'}})
    with pdf.open(changed['path']) as doc:
        spans=[span for item in doc[0].get_text('dict')['blocks'] if item['type']==0 for line in item['lines'] for span in line['spans']]
        bold=next(span for span in spans if 'bold' in span['text']);plain=next(span for span in spans if 'Normal' in span['text'])
        assert abs(bold['size']-36)<.1 and abs(plain['size']-28)<.1
        assert all(abs((span['color']&255)-170)<=1 for span in spans)
