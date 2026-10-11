import json
import sys
from pathlib import Path
import pytest
import pymupdf as pdf
import pypdfium2 as pdfium
from PIL import Image

sys.path.insert(0,str(Path(__file__).resolve().parents[1] / 'worker'))
from engine import Engine, PDFError, fingerprint


@pytest.fixture
def fixture(tmp_path):
    source=tmp_path / 'source with spaces - résumé.pdf'
    doc=pdf.open()
    for number in range(3):
        page=doc.new_page(width=400,height=500)
        page.insert_text((40,60),f'Page {number+1} fixture content',fontsize=12)
        page.insert_text((40,100),'SecretData 12345',fontsize=12)
        page.draw_rect(pdf.Rect(30,30,370,140),color=(0,0,1))
    page=doc[0]
    field=pdf.Widget();field.field_name='FullName';field.field_type=pdf.PDF_WIDGET_TYPE_TEXT
    field.rect=pdf.Rect(40,160,280,190);field.field_value='Initial'
    page.add_widget(field)
    doc.set_metadata({'title':'Fixture title','author':'Synthetic test'})
    doc.set_toc([[1,'Start',1],[1,'Finish',3]])
    doc.embfile_add('notes.txt',b'SecretData inside an attachment')
    doc.save(source);doc.close()
    engine=Engine(tmp_path / 'working')
    session=engine.dispatch({'command':'open','args':{'path':str(source)}})
    return engine,session,source


def apply(engine,session,operation,**args):
    return engine.dispatch({'command':'apply','session':session['id'],'revision':session['revision'],'args':{'operation':operation,**args}})


def test_open_preserves_original_and_pdfium_renders(fixture):
    engine,session,source=fixture
    assert Path(session['path']).read_bytes()==source.read_bytes()
    assert session['page_count']==3 and session['metadata']['title']=='Fixture title'
    assert not session['dirty']
    with pdfium.PdfDocument(session['path']) as independent:
        assert len(independent)==3
        bitmap=independent[0].render(scale=1)
        assert bitmap.width==400 and bitmap.height==500


def test_revision_rotate_undo_redo_recovery(fixture):
    engine,session,source=fixture; baseline=fingerprint(source)
    rotated=apply(engine,session,'rotate',pages='2',degrees=90)
    assert rotated['pages'][1]['rotation']==90 and rotated['dirty']
    with pytest.raises(PDFError,match='changed'):
        apply(engine,session,'rotate',pages='1')
    undone=engine.dispatch({'command':'undo','session':session['id'],'revision':rotated['revision']})
    assert undone['pages'][1]['rotation']==0
    redone=engine.dispatch({'command':'redo','session':session['id'],'revision':undone['revision']})
    recovered=Engine(engine.root).dispatch({'command':'info','session':session['id']})
    assert recovered['path']==redone['path'] and recovered['can_undo']
    assert fingerprint(source)==baseline


def test_failed_edit_is_transactional(fixture):
    engine,session,source=fixture
    with pytest.raises(PDFError,match='at least one'):
        apply(engine,session,'delete_pages',pages='all')
    assert engine.dispatch({'command':'info','session':session['id']})['revision']==0
    with pytest.raises(PDFError,match='does not fit'):
        apply(engine,session,'replace_text',page=1,rect=[40,80,55,101],text='A very long replacement',size=24)
    with pdf.open(session['path']) as doc:
        assert 'SecretData' in doc[0].get_text()


def test_replace_text_removes_original_preserves_graphics(fixture):
    engine,session,_=fixture
    modified=apply(engine,session,'replace_text',page=1,rect=[39,85,180,105],text='Replacement',size=12)
    with pdf.open(modified['path']) as doc:
        assert 'Replacement' in doc[0].get_text()
        assert 'SecretData' not in doc[0].get_text()
        assert len(doc[0].get_drawings())==1
        assert doc.metadata['title']=='Fixture title'


def test_page_ranges_reorder_extract_and_merge(fixture,tmp_path):
    engine,session,_=fixture
    reordered=apply(engine,session,'reorder',pages='3,1,2,1')
    assert reordered['page_count']==4
    with pdf.open(reordered['path']) as doc:
        assert 'Page 3' in doc[0].get_text() and 'Page 1' in doc[3].get_text()
    output=tmp_path/'extracted.pdf'
    engine.dispatch({'command':'export','session':session['id'],'args':{'path':str(output),'mode':'extract','pages':'1,3'}})
    with pdf.open(output) as doc:
        assert len(doc)==2
    merged=apply(engine,reordered,'merge',paths=[str(output)])
    assert merged['page_count']==6


def test_fields_are_interactive_after_save_and_flatten(fixture,tmp_path):
    engine,session,_=fixture
    fields=engine.dispatch({'command':'inspect_page','session':session['id'],'args':{'page':1}})['forms']
    filled=apply(engine,session,'fill_forms',values={fields[0]['id']:'Updated name'})
    with pdf.open(filled['path']) as doc:
        field=next(doc[0].widgets());assert field.field_value=='Updated name'
        assert field.field_name=='FullName'
    with pdfium.PdfDocument(filled['path']) as independent:
        independent.init_forms()
        assert independent[0].render(scale=1,may_draw_forms=True).width==400
    flattened=apply(engine,filled,'flatten_forms')
    with pdf.open(flattened['path']) as doc:
        assert not list(doc[0].widgets() or [])
        assert 'Updated name' in doc[0].get_text()


def test_redaction_removes_target_auxiliary_content(fixture):
    engine,session,source=fixture; original=fingerprint(source)
    redacted=apply(engine,session,'redact',page=1,rect=[39,85,180,105])
    with pdf.open(redacted['path']) as doc:
        assert 'SecretData' not in doc[0].get_text()
        assert doc.embfile_count()==0 and doc.metadata['author']==''
        assert 'Page 1' in doc[0].get_text()
    with pdfium.PdfDocument(redacted['path']) as independent:
        assert 'SecretData' not in independent[0].get_textpage().get_text_range()
    assert fingerprint(source)==original


def test_export_encryption_password_and_original_guard(fixture,tmp_path):
    engine,session,source=fixture
    output=tmp_path/'protected.pdf'
    engine.dispatch({'command':'export','session':session['id'],'args':{'path':str(output),'mode':'protect','password':'test password'}})
    with pdf.open(output) as doc:
        assert doc.needs_pass and not doc.authenticate('wrong') and doc.authenticate('test password')
    with pdfium.PdfDocument(output,password='test password') as independent:
        assert len(independent)==3
    with pytest.raises(PDFError,match='new name'):
        engine.dispatch({'command':'export','session':session['id'],'args':{'path':str(source)}})
    reopened=engine.dispatch({'command':'open','args':{'path':str(output),'password':'test password'}})
    assert reopened['page_count']==3


@pytest.mark.parametrize('mode',['docx','pptx','pptx_images','txt','markdown'])
def test_editable_and_text_exports(fixture,tmp_path,mode):
    engine,session,_=fixture
    output=tmp_path/f'output.{mode}'
    engine.dispatch({'command':'export','session':session['id'],'args':{'path':str(output),'mode':mode}})
    assert output.stat().st_size>100
    if mode=='docx':
        from docx import Document
        assert any('SecretData' in p.text for p in Document(output).paragraphs)
    elif mode=='pptx':
        from pptx import Presentation
        slides=Presentation(output).slides
        assert len(slides)==3 and any('SecretData' in s.text for s in slides[0].shapes if s.has_text_frame)
    elif mode=='pptx_images':
        from pptx import Presentation
        assert len(Presentation(output).slides[0].shapes)==1
    else:
        assert 'SecretData' in output.read_text(encoding='utf-8')


def test_add_text_annotation_field_crop_number_and_image(fixture,tmp_path):
    engine,session,_=fixture
    updated=apply(engine,session,'add_text',page=1,rect=[40,210,300,250],text='Added text',size=12)
    updated=apply(engine,updated,'highlight',page=1,rect=[40,45,220,64])
    updated=apply(engine,updated,'add_form',page=2,rect=[40,160,200,190],name='NewField')
    updated=apply(engine,updated,'page_numbers',pages='all')
    updated=apply(engine,updated,'crop',pages='3',margin=10)
    image=tmp_path/'image.png';Image.new('RGB',(40,40),'red').save(image)
    updated=apply(engine,updated,'add_image',page=1,rect=[40,280,100,340],path=str(image))
    with pdf.open(updated['path']) as doc:
        assert 'Added text' in doc[0].get_text()
        assert len(list(doc[0].annots()))==1
        assert next(doc[1].widgets()).field_name=='NewField'
        assert doc[2].rect.width==380
        assert len(doc[0].get_images())==1


def test_image_creation_and_export(fixture,tmp_path):
    engine,_,_=fixture
    image=tmp_path/'sample.png';Image.new('RGB',(100,80),'white').save(image)
    session=engine.dispatch({'command':'create','args':{'images':[str(image)]}})
    assert session['page_count']==1
    output=engine.dispatch({'command':'export_images','session':session['id'],'args':{'folder':str(tmp_path/'images'),'dpi':72}})
    with Image.open(output['paths'][0]) as rendered:
        # The image has default 96-DPI physical dimensions, rendered at 72 DPI.
        assert rendered.size==(75,60)


@pytest.mark.parametrize('rotation', [0, 90])
def test_ocr_preserves_scan_pixels_and_digital_pages(tmp_path, rotation):
    original=pdf.open(); page=original.new_page(width=400,height=500)
    page.insert_text((40,70),'Offline OCR sample 67890',fontsize=22)
    image=page.get_pixmap(dpi=150).tobytes('png')
    original.close()
    source=tmp_path/'scanned.pdf'; doc=pdf.open(); page=doc.new_page(width=400,height=500)
    page.insert_image(page.rect,stream=image); page.draw_rect(pdf.Rect(30,30,370,100),color=(0,0,1))
    page.set_rotation(rotation)
    page=doc.new_page();page.insert_text((40,70),'Digital text stays unchanged',fontsize=12)
    doc.save(source);doc.close()
    engine=Engine(tmp_path/'working'); session=engine.dispatch({'command':'open','args':{'path':str(source)}})
    with pdfium.PdfDocument(source) as before:
        pixels=before[0].render(scale=1).to_pil().tobytes()
    changed=apply(engine,session,'ocr',pages='all')
    with pdfium.PdfDocument(changed['path']) as after:
        assert '67890' in after[0].get_textpage().get_text_range()
        assert after[0].render(scale=1).to_pil().tobytes()==pixels
        assert after[1].get_textpage().get_text_range().count('Digital text')==1
    again=apply(engine,changed,'ocr',pages='all')
    with pdf.open(again['path']) as result:
        assert result[0].get_text().count('67890')==1
        assert result[0].rotation==rotation


def test_image_replace_remove_extract_jpg_and_lossy_export(fixture,tmp_path):
    engine,session,source=fixture
    original_hash=fingerprint(source)
    import random
    image=tmp_path/'noisy.png';Image.frombytes('RGB',(1200,900),random.Random(123).randbytes(1200*900*3)).save(image)
    changed=apply(engine,session,'add_image',rect=[40,210,340,435],path=str(image))
    info=engine.dispatch({'command':'inspect_page','session':session['id'],'args':{'page':1}})
    xref=info['images'][0]['id']
    extracted=engine.dispatch({'command':'export_images','session':session['id'],'args':{'folder':str(tmp_path/'extracted'),'format':'embedded'}})
    with Image.open(extracted['paths'][0]) as saved:
        assert saved.size==(1200,900)
    jpg=engine.dispatch({'command':'export_images','session':session['id'],'args':{'folder':str(tmp_path/'jpg'),'format':'jpg','pages':'1'}})
    with Image.open(jpg['paths'][0]) as saved:
        assert saved.format=='JPEG'
    small=tmp_path/'small.pdf'
    engine.dispatch({'command':'export','session':session['id'],'args':{'path':str(small),'mode':'compress_screen'}})
    assert small.stat().st_size < Path(changed['path']).stat().st_size*.5
    with pdfium.PdfDocument(small) as independent:
        assert len(independent)==3 and 'SecretData' in independent[0].get_textpage().get_text_range()
    replacement=tmp_path/'replacement.png';Image.new('RGB',(60,40),'red').save(replacement)
    changed=apply(engine,changed,'replace_image',page=1,id=xref,path=str(replacement))
    with pdf.open(changed['path']) as doc:
        assert doc[0].get_image_info()[0]['width']==60
    changed=apply(engine,changed,'delete_image',page=1,id=xref)
    assert fingerprint(source)==original_hash


def test_annotation_lifecycle_and_choice_fields(fixture):
    engine,session,_=fixture
    changed=apply(engine,session,'underline',page=1,rect=[40,45,300,64])
    changed=apply(engine,changed,'strikeout',page=1,rect=[40,85,300,104])
    info=engine.dispatch({'command':'inspect_page','session':session['id'],'args':{'page':1}})
    target=info['annotations'][0]['id']
    changed=apply(engine,changed,'edit_annotation',page=1,id=target,text='Review this line')
    changed=apply(engine,changed,'delete_annotation',page=1,id=target)
    changed=apply(engine,changed,'add_form',page=2,rect=[40,170,250,200],name='Department',field_type='combo',choices='Alpha\nBeta')
    changed=apply(engine,changed,'add_form',page=2,rect=[40,220,60,240],name='Agreed',field_type='checkbox')
    info=engine.dispatch({'command':'inspect_page','session':session['id'],'args':{'page':2}})
    values={field['id']:('Beta' if field['name']=='Department' else field['states']['normal'][-1]) for field in info['forms']}
    changed=apply(engine,changed,'fill_forms',values=values)
    with pdf.open(changed['path']) as doc:
        assert len(list(doc[0].annots()))==1
        assert next(doc[1].widgets()).field_value=='Beta'


def test_comparison_same_changed_and_extra_page(fixture,tmp_path):
    engine,session,source=fixture
    same=engine.dispatch({'command':'compare','session':session['id'],'args':{'path':str(source)}})
    assert same['changed_pages']==0
    changed=apply(engine,session,'replace_text',page=1,rect=[38,83,230,106],text='PublicData 54321',size=12)
    changed=apply(engine,changed,'insert_blank')
    result=engine.dispatch({'command':'compare','session':session['id'],'args':{'path':str(source)}})
    assert result['changed_pages']==2
    assert 'PublicData' in result['pages'][0]['text_diff']
    assert result['pages'][0]['pixel_ratio']>0
    assert result['pages'][3]['dimensions_changed']
    output=tmp_path/'report.html'
    engine.dispatch({'command':'save_report','session':session['id'],'args':{'report':result['report'],'path':str(output)}})
    assert 'data:image/png;base64,' in output.read_text(encoding='utf-8')


def test_print_preparation_keeps_page_order_and_dimensions(fixture):
    engine,session,_=fixture
    changed=apply(engine,session,'rotate',pages='2',degrees=90)
    result=engine.dispatch({'command':'prepare_print','session':session['id'],'args':{'pages':'2,1'}})
    assert [item['page'] for item in result]==[2,1]
    assert (result[0]['width'],result[0]['height'])==(500,400)
    assert result[0]['dpi']==150
    with Image.open(result[0]['path']) as image:
        assert image.width>image.height
    assert engine.dispatch({'command':'info','session':session['id']})['revision']==changed['revision']


@pytest.mark.parametrize('rotation',[90,180,270])
def test_visual_edit_on_rotated_cropped_page(fixture,rotation):
    engine,session,source=fixture;original=fingerprint(source)
    changed=apply(engine,session,'crop',pages='1',margin=10)
    changed=apply(engine,changed,'rotate',pages='1',degrees=rotation)
    dimensions=(changed['pages'][0]['width'],changed['pages'][0]['height'])
    changed=apply(engine,changed,'rectangle',page=1,rect=[100,100,180,145],color='#ff0000')
    assert (changed['pages'][0]['width'],changed['pages'][0]['height'])==dimensions
    with pdf.open(changed['path']) as doc:
        page=doc[0]  # Annotation objects retain weak references to their parent page.
        assert 'SecretData' in page.get_text()
        assert (list(page.annots())[0].rect*page.rotation_matrix).contains(pdf.Rect(100,100,180,145))
        assert next(page.widgets()).field_value=='Initial'
    with pdfium.PdfDocument(changed['path']) as independent:
        image=independent[0].render(scale=1).to_pil().convert('RGB')
        assert image.size==tuple(map(int,dimensions))
        assert sum(r>180 and r>g+50 and r>b+50 for r,g,b in image.crop((98,98,183,148)).get_flattened_data())>50
    assert fingerprint(source)==original


@pytest.mark.parametrize('rotation',[90,270])
def test_redaction_and_added_text_use_visual_rotated_coordinates(fixture,rotation):
    engine,session,_=fixture
    changed=apply(engine,session,'crop',pages='1',margin=10)
    changed=apply(engine,changed,'rotate',pages='1',degrees=rotation)
    hits=engine.dispatch({'command':'search','session':session['id'],'args':{'text':'SecretData 12345'}})
    target=next(hit for hit in hits if hit['page']==1)['rect']
    changed=apply(engine,changed,'redact',page=1,rect=target)
    changed=apply(engine,changed,'add_text',page=1,rect=[100,180,340,225],text='Visual coordinates verified',size=12)
    with pdfium.PdfDocument(changed['path']) as doc:
        text=doc[0].get_textpage().get_text_range()
        assert 'SecretData' not in text
        assert 'Visual coordinates verified' in text


@pytest.mark.parametrize('rotation',[90,180,270])
def test_page_numbers_on_rotated_pages_have_visual_footer_position(fixture,rotation):
    engine,session,_=fixture
    changed=apply(engine,session,'rotate',pages='1',degrees=rotation)
    changed=apply(engine,changed,'page_numbers',pages='1',start=9001)
    with pdf.open(changed['path']) as doc:
        page=doc[0];bounds=page.search_for('9001')[0]*page.rotation_matrix
        assert bounds.y0>page.rect.height-40
    with pdfium.PdfDocument(changed['path']) as independent:
        assert '9001' in independent[0].get_textpage().get_text_range()

@pytest.mark.parametrize('rotation',[0,90,180,270])
def test_ink_stamp_rotation_reopen_and_removal(tmp_path, rotation):
    source=tmp_path/'annotation-source.pdf'
    doc=pdf.open();page=doc.new_page(width=400,height=500)
    page.set_cropbox(pdf.Rect(20,30,380,470));page.set_rotation(rotation)
    doc.save(source);doc.close();baseline=fingerprint(source)
    engine=Engine(tmp_path/'working');session=engine.dispatch({'command':'open','args':{'path':str(source)}})
    strokes=[[[50,60],[100,70],[140,60]],[[80,90],[80,150]]]
    session=apply(engine,session,'ink',strokes=strokes,width=3,color='#cc0000')
    with pdf.open(session['path']) as result:
        page=result[0];annotation=page.first_annot
        assert annotation.type[1]=='Ink'
        actual=[[list(pdf.Point(p)*page.rotation_matrix) for p in stroke] for stroke in annotation.vertices]
        for expected,found in zip(strokes,actual):
            for a,b in zip(expected,found):assert a==pytest.approx(b,abs=.1)
    session=apply(engine,session,'stamp',rect=[40,180,260,260],stamp='approved',color='#006633')
    with pdf.open(session['path']) as result:
        page=result[0];annotations=list(page.annots())
        assert [a.type[1] for a in annotations]==['Ink','Stamp']
        stamp_rect=annotations[1].rect*page.rotation_matrix
        assert page.rect.contains(stamp_rect)
    output=tmp_path/'annotated.pdf'
    engine.dispatch({'command':'export','session':session['id'],'args':{'path':str(output),'mode':'pdf'}})
    with pdfium.PdfDocument(str(output)) as independent:
        image=independent[0].render(scale=1,draw_annots=True).to_pil().convert('RGB')
        assert sum(1 for r,g,b in image.get_flattened_data() if r>120 and g<100 and b<100)>50
    inspected=engine.dispatch({'command':'inspect_page','session':session['id'],'args':{'page':1}})
    session=apply(engine,session,'delete_annotation',id=inspected['annotations'][0]['id'])
    with pdf.open(session['path']) as result:
        page=result[0];assert [a.type[1] for a in page.annots()]==['Stamp']
    assert fingerprint(source)==baseline


def test_ink_rejects_invalid_points_without_revision(fixture):
    engine,session,source=fixture
    for strokes in ([[[-5,2],[10,20]]],[[[1,2],[float('nan'),3]]],[[[1,2]]]):
        with pytest.raises(PDFError):apply(engine,session,'ink',strokes=strokes)
        assert engine.dispatch({'command':'info','session':session['id']})['revision']==session['revision']
