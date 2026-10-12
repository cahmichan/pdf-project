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


@pytest.mark.parametrize('rotation',[0,90,180,270])
def test_form_geometry_flags_fill_reopen_and_readonly_limits(tmp_path,rotation):
    source=tmp_path/'interactive-fields.pdf';doc=pdf.open();page=doc.new_page(width=400,height=500)
    page.set_cropbox(pdf.Rect(20,30,380,470));page.set_rotation(rotation)
    specifications=[('Name',pdf.PDF_WIDGET_TYPE_TEXT,[40,40,180,70],'Old',0),
                    ('Notes',pdf.PDF_WIDGET_TYPE_TEXT,[40,100,260,155],'Line one',pdf.PDF_TX_FIELD_IS_MULTILINE),
                    ('Consent',pdf.PDF_WIDGET_TYPE_CHECKBOX,[40,190,60,210],False,0),
                    ('Category',pdf.PDF_WIDGET_TYPE_COMBOBOX,[40,240,170,270],'First',0),
                    ('Selection',pdf.PDF_WIDGET_TYPE_LISTBOX,[200,240,320,300],'First',0),
                    ('Locked',pdf.PDF_WIDGET_TYPE_TEXT,[40,300,180,330],'Fixed',pdf.PDF_FIELD_IS_READ_ONLY)]
    for name,kind,rect,value,flags in specifications:
        widget=pdf.Widget();widget.field_name=name;widget.field_type=kind;widget.rect=pdf.Rect(rect);widget.field_value=value;widget.field_flags=flags
        if name=='Name':widget.text_maxlen=8
        if kind in (pdf.PDF_WIDGET_TYPE_COMBOBOX,pdf.PDF_WIDGET_TYPE_LISTBOX):widget.choice_values=['First','Second']
        page.add_widget(widget)
    doc.save(source);doc.close();baseline=fingerprint(source)
    engine=Engine(tmp_path/'working');session=engine.open_file({'path':str(source)})
    fields={field['name']:field for field in engine.inspect_page(engine.session(session['id']),{'page':1})['forms']}
    assert fields['Notes']['multiline'] and fields['Locked']['read_only'] and fields['Name']['max_length']==8
    with pdf.open(source) as doc:
        page=doc[0]
        for widget in page.widgets():assert fields[widget.field_name]['rect']==pytest.approx(list(widget.rect*page.rotation_matrix))
    for name,value in [('Locked','Changed'),('Name','Too many characters')]:
        with pytest.raises(PDFError):apply(engine,session,'fill_forms',values={fields[name]['id']:value})
        assert engine.info(engine.session(session['id']))['revision']==session['revision']
    values={fields[name]['id']:value for name,value in [('Name','NewName'),('Notes','First line\nSecond line'),('Consent','Yes'),('Category','Second'),('Selection','Second'),('Locked','Fixed')]}
    session=apply(engine,session,'fill_forms',values=values)
    output=tmp_path/'filled-fields.pdf';engine.export(engine.session(session['id']),{'path':str(output)})
    with pdf.open(output) as doc:
        actual={widget.field_name:widget.field_value for widget in doc[0].widgets()}
        assert actual=={'Name':'NewName','Notes':'First line\nSecond line','Consent':'Yes','Category':'Second','Selection':'Second','Locked':'Fixed'}
    with pdfium.PdfDocument(str(output)) as independent:
        independent.init_forms();assert independent[0].render(scale=1,draw_annots=True).to_pil().size==((440,360) if rotation in (90,270) else (360,440))
    undone=engine.dispatch({'command':'undo','session':session['id'],'revision':session['revision']})
    with pdf.open(undone['path']) as doc:assert {widget.field_name:widget.field_value for widget in doc[0].widgets()}['Name']=='Old'
    assert fingerprint(source)==baseline


def test_shared_form_widgets_update_appearances_on_every_page(tmp_path):
    source=tmp_path/'shared-fields.pdf';doc=pdf.open()
    for index in range(2):
        page=doc.new_page(width=300,height=300);field=pdf.Widget();field.field_name='SharedName';field.field_type=pdf.PDF_WIDGET_TYPE_TEXT
        field.rect=pdf.Rect(30,50,250,90);field.field_value='Initial';field.text_fontsize=12;page.add_widget(field)
    doc.save(source);doc.close();baseline=fingerprint(source)
    engine=Engine(tmp_path/'working');session=engine.open_file({'path':str(source)})
    field=engine.inspect_page(engine.session(session['id']),{'page':1})['forms'][0]
    session=apply(engine,session,'fill_forms',values={field['id']:'Shared new value'})
    with pdf.open(session['path']) as doc:
        assert [widget.field_value for page in doc for widget in page.widgets()]==['Shared new value','Shared new value']
    session=apply(engine,session,'flatten_forms')
    with pdfium.PdfDocument(session['path']) as independent:
        for page in independent:assert 'Shared new value' in page.get_textpage().get_text_range()
    assert fingerprint(source)==baseline


@pytest.mark.parametrize('rotation',[0,90,180,270])
@pytest.mark.parametrize('origin',[(0,0),(-30,-60),(20,30)])
@pytest.mark.parametrize('mode',['margins','selection'])
def test_precise_crop_visual_pixels_offset_media_reset_and_save(tmp_path,rotation,origin,mode):
    source=tmp_path/'crop-source.pdf';doc=pdf.open();page=doc.new_page(width=400,height=500)
    page.draw_rect(pdf.Rect(50,80,280,390),color=(1,0,0),fill=(.2,.6,.8))
    page.insert_text((70,160),'Preserved crop content',fontsize=12)
    page.set_mediabox(pdf.Rect(origin[0],origin[1],origin[0]+400,origin[1]+500))
    page.set_cropbox(pdf.Rect(origin[0]+10,20,origin[0]+390,480));page.set_rotation(rotation)
    dimensions=(page.rect.width,page.rect.height);doc.save(source);doc.close();baseline=fingerprint(source)
    engine=Engine(tmp_path/'working');session=engine.open_file({'path':str(source)})
    with pdfium.PdfDocument(str(source)) as independent:before=independent[0].render(scale=1).to_pil().convert('RGB')
    args={'crop_mode':mode}
    if mode=='margins':args['margins']={'left':11,'top':17,'right':23,'bottom':29}
    else:args['rect']=[11,17,dimensions[0]-23,dimensions[1]-29]
    session=apply(engine,session,'crop',**args)
    assert session['pages'][0]['width']==dimensions[0]-34
    assert session['pages'][0]['height']==dimensions[1]-46
    with pdfium.PdfDocument(session['path']) as independent:
        image=independent[0].render(scale=1).to_pil().convert('RGB')
        assert image.tobytes()==before.crop((11,17,before.width-23,before.height-29)).tobytes()
    # Repeated trimming operates relative to the current visible crop.
    session=apply(engine,session,'crop',margins=dict.fromkeys(('left','top','right','bottom'),5))
    assert session['pages'][0]['width']==dimensions[0]-44
    session=apply(engine,session,'crop',crop_mode='reset')
    expected=(500,400) if rotation in (90,270) else (400,500)
    assert (session['pages'][0]['width'],session['pages'][0]['height'])==expected
    output=tmp_path/'crop-reset.pdf';engine.export(engine.session(session['id']),{'path':str(output)})
    with pdfium.PdfDocument(str(output)) as independent:
        image=independent[0].render(scale=1).to_pil();assert image.size==expected
    assert fingerprint(source)==baseline


def test_precise_crop_rejects_invalid_geometry_atomically(fixture):
    engine,session,source=fixture
    for settings in ({'margins':{'left':-1,'right':0,'top':0,'bottom':0}},
                     {'margins':{'left':float('nan'),'right':0,'top':0,'bottom':0}},
                     {'margins':{'left':400,'right':0,'top':0,'bottom':0}},
                     {'margins':{'left':0}}, {'crop_mode':'selection','rect':[1,1,401,499]},
                     {'crop_mode':'selection','rect':[0,0,float('inf'),3]}):
        with pytest.raises(PDFError):apply(engine,session,'crop',**settings)
        assert engine.dispatch({'command':'info','session':session['id']})['revision']==session['revision']


@pytest.mark.parametrize('rotation',[0,90,180,270])
@pytest.mark.parametrize('position',['top','middle','bottom'])
@pytest.mark.parametrize('align',['left','right'])
def test_custom_number_format_and_visual_alignment(fixture,rotation,position,align,tmp_path):
    engine,session,source=fixture;baseline=fingerprint(source)
    session=apply(engine,session,'crop',pages='all',margin=10)
    session=apply(engine,session,'rotate',pages='all',degrees=rotation)
    session=apply(engine,session,'page_numbers',pages='3,1',start=7,number_format='Leaf {n}/{total} ({page}/{pages})',
                  position=position,align=align,size=10,inset=18,edge=15,color='#aa0000',opacity=.8)
    expected={0:'Leaf 8/2 (1/3)',2:'Leaf 7/2 (3/3)'}
    with pdf.open(session['path']) as doc:
        for index,text in expected.items():
            page=doc[index];rect=page.search_for(text)[0]*page.rotation_matrix
            if position=='top':assert 10<rect.y0<30
            elif position=='bottom':assert page.rect.height-35<rect.y0<page.rect.height-10
            else:assert abs((rect.y0+rect.y1)/2-page.rect.height/2)<10
            if align=='left':assert rect.x0==pytest.approx(18,abs=1)
            else:assert rect.x1==pytest.approx(page.rect.width-18,abs=1)
        assert 'Leaf' not in doc[1].get_text()
    output=tmp_path/'numbered.pdf';engine.export(engine.session(session['id']),{'path':str(output)})
    with pdfium.PdfDocument(str(output)) as independent:
        for index,text in expected.items():assert text in independent[index].get_textpage().get_text_range()
    assert fingerprint(source)==baseline


def test_numbering_and_watermark_settings_reject_invalid_values(fixture):
    engine,session,source=fixture
    for settings in ({'start':1.5},{'number_format':'{unknown}'},{'opacity':2},{'size':float('nan')},{'inset':250},{'position':'diagonal'}):
        with pytest.raises(PDFError):apply(engine,session,'page_numbers',**settings)
        assert engine.dispatch({'command':'info','session':session['id']})['revision']==session['revision']
    session=apply(engine,session,'watermark',pages='1',text='Review copy',position='top',align='right',size=15,opacity=.4)
    with pdf.open(session['path']) as doc:
        page=doc[0];rect=page.search_for('Review copy')[0];assert rect.y0<30 and rect.x1==pytest.approx(page.rect.width-24,abs=1)


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


@pytest.mark.parametrize('rotation',[0,90,180,270])
@pytest.mark.parametrize('mode',['reorder','extract'])
def test_copied_rotated_cropped_page_links_and_rendering(fixture,tmp_path,rotation,mode):
    engine,session,source=fixture
    linked=tmp_path/'rotated-links.pdf'
    with pdf.open(source) as doc:
        for page in doc:
            page.set_cropbox(pdf.Rect(20,20,380,480));page.set_rotation(rotation)
        doc[0].insert_link({'kind':pdf.LINK_GOTO,'from':pdf.Rect(40,230,140,255),'page':2,'to':pdf.Point(70,110)})
        doc[0].insert_link({'kind':pdf.LINK_URI,'from':pdf.Rect(40,260,140,285),'uri':'https://example.org/'})
        doc.save(linked)
    baseline=fingerprint(linked)
    with pdf.open(linked) as doc:
        expected=doc[0].get_links();dimensions=list(doc[0].rect)
    session=engine.dispatch({'command':'open','args':{'path':str(linked)}})
    if mode=='reorder':
        session=apply(engine,session,'reorder',pages=[1,1,3]);output=session['path']
    else:
        output=str(tmp_path/'extracted-copies.pdf')
        engine.dispatch({'command':'export','session':session['id'],'args':{'path':output,'mode':'extract','pages':[1,1,3]}})
    with pdf.open(output) as doc:
        assert doc.page_xref(0)!=doc.page_xref(1)
        for index in (0,1):
            assert list(doc[index].rect)==pytest.approx(dimensions)
            links=doc[index].get_links();assert len(links)==2
            for found,wanted in zip(links,expected):
                assert list(found['from'])==pytest.approx(list(wanted['from']),abs=.01)
                if found['kind']==pdf.LINK_GOTO:
                    assert found['page']==2
                    assert list(found['to'])==pytest.approx(list(wanted['to']),abs=.01)
                else:assert found['uri']==wanted['uri']
    with pdfium.PdfDocument(output) as independent:
        assert independent[0].render(scale=1).to_pil().tobytes()==independent[1].render(scale=1).to_pil().tobytes()
    assert fingerprint(linked)==baseline


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


@pytest.mark.parametrize('settings,groups',[
    ({'mode':'individual'},[[1],[2],[3]]),
    ({'mode':'every','size':2},[[1,2],[3]]),
    ({'mode':'ranges','ranges':'3,1;1,1;2-3'},[[3,1],[1,1],[2,3]])])
def test_split_groups_outputs_receipt_and_source_preservation(fixture,tmp_path,settings,groups):
    engine,session,source=fixture;baseline=fingerprint(source)
    def run():return engine.dispatch({'command':'split','session':session['id'],'revision':session['revision'],'args':{**settings,'folder':str(tmp_path/'parts')}})
    result=run();assert [item['pages'] for item in result['items']]==groups
    assert result['status']=='finished'
    assert json.loads(Path(result['manifest']).read_text(encoding='utf-8'))==result
    for item in result['items']:
        assert item['status']=='done'
        with pdf.open(item['output']) as doc:
            assert len(doc)==len(item['pages'])
            assert len(set(doc.page_xref(index) for index in range(len(doc))))==len(doc)
            for page,number in zip(doc,item['pages']):assert f'Page {number} fixture' in page.get_text()
        with pdfium.PdfDocument(item['output']) as doc:
            assert len(doc)==len(item['pages']);assert doc[0].render(scale=.5).width==200
    again=run();assert not {item['output'] for item in result['items']} & {item['output'] for item in again['items']}
    assert fingerprint(source)==baseline
    assert engine.dispatch({'command':'info','session':session['id']})['revision']==session['revision']


def test_split_invalid_groups_and_stale_revision_create_no_outputs(fixture,tmp_path):
    engine,session,source=fixture;folder=tmp_path/'invalid-parts'
    for settings in ({'mode':'every','size':0},{'mode':'every','size':1.5},{'mode':'ranges','ranges':'1;9'}, {'mode':'ranges','ranges':'1;'}, {'mode':'unknown'}):
        with pytest.raises(PDFError):engine.dispatch({'command':'split','session':session['id'],'revision':session['revision'],'args':{**settings,'folder':str(folder)}})
        assert not folder.exists()
    changed=apply(engine,session,'rotate',pages='1')
    with pytest.raises(PDFError):engine.dispatch({'command':'split','session':changed['id'],'revision':session['revision'],'args':{'folder':str(folder)}})
    assert not folder.exists()


def test_split_failure_receipt_and_interrupted_history(fixture,tmp_path,monkeypatch):
    from workflows import history
    engine,session,source=fixture;export=engine.export;calls=0
    def failing(current,args):
        nonlocal calls
        calls+=1
        if calls==2:raise PDFError('Synthetic second-file failure')
        return export(current,args)
    monkeypatch.setattr(engine,'export',failing)
    request={'command':'split','session':session['id'],'revision':session['revision'],'args':{'folder':str(tmp_path/'partial')}}
    result=engine.dispatch(request)
    assert [item['status'] for item in result['items']]==['done','failed','done']
    assert result['items'][1]['error']=='Synthetic second-file failure'
    assert json.loads(Path(result['manifest']).read_text(encoding='utf-8'))==result
    calls=0
    def interrupted(current,args):
        nonlocal calls
        calls+=1
        if calls==2:raise KeyboardInterrupt()
        return export(current,args)
    monkeypatch.setattr(engine,'export',interrupted)
    with pytest.raises(KeyboardInterrupt):engine.dispatch(request)
    jobs=history(engine.root)
    stopped=next(job for job in jobs if job['status']=='interrupted')
    assert stopped['items'][0]['status']=='done' and Path(stopped['items'][0]['output']).is_file()
    assert stopped['items'][1]['status']=='running'

@pytest.mark.parametrize('order',[[1,1,3],[3,1,1],[1,3,1],[1,1,1,3]])
def test_duplicate_pages_edit_independently_and_preserve_links_forms_bookmarks(fixture,order):
    engine,session,source=fixture;baseline=fingerprint(source)
    # Add a link to page 3 so both retained and copied links can be checked.
    with pdf.open(source) as original:
        original[0].insert_link({'kind':pdf.LINK_GOTO,'from':pdf.Rect(40,250,150,280),'page':2,'to':pdf.Point(40,80)})
        linked=source.parent/'linked.pdf';original.save(linked)
    session=engine.dispatch({'command':'open','args':{'path':str(linked)}})
    session=apply(engine,session,'reorder',pages=order)
    indices=[i for i,n in enumerate(order) if n==1];first,copy=indices[0],indices[-1]
    with pdf.open(session['path']) as doc:
        assert len(set(doc.page_xref(n) for n in range(len(doc))))==len(doc)
        assert [link['page'] for link in doc[first].get_links()]==[order.index(3)]
        assert [link['page'] for link in doc[copy].get_links()]==[order.index(3)]
        assert dict((entry[1],entry[2]) for entry in doc.get_toc())['Finish']==order.index(3)+1
        fields=[[w.field_name for w in p.widgets() or []] for p in doc]
        assert fields[first]==['FullName'] and fields[copy]==[f'FullName_copy{len(indices)-1}']
        copied_field=list(doc[copy].widgets())[0].xref
    session=apply(engine,session,'add_text',page=copy+1,rect=[40,320,280,355],text='Independent copied page')
    session=apply(engine,session,'fill_forms',values={str(copied_field):'Copied person'})
    with pdf.open(session['path']) as doc:
        assert 'Independent copied page' not in doc[first].get_text()
        assert 'Independent copied page' in doc[copy].get_text()
        assert [w.field_value for w in doc[first].widgets() or []]==['Initial']
        assert [w.field_value for w in doc[copy].widgets() or []]==['Copied person']
    undone=engine.dispatch({'command':'undo','session':session['id'],'revision':session['revision']})
    with pdf.open(undone['path']) as doc:assert [w.field_value for w in doc[copy].widgets() or []]==['Initial']
    assert fingerprint(source)==baseline
