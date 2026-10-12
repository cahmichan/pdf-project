import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'worker'))
import pytest
import pymupdf as pdf
import pypdfium2 as pdfium
from engine import Engine,PDFError,fingerprint,tessdata_dir
from ocr import validate_language


def scan(path,chinese=False):
    with pdf.open() as doc:
        page=doc.new_page(width=500,height=300)
        if chinese:
            page.insert_font(fontname='CJKSource',fontbuffer=pdf.Font('cjk').buffer)
            page.insert_text((40,80),'文件扫描测试 86420',fontsize=30,fontname='CJKSource')
            page.insert_text((40,160),'Reference document 86420',fontsize=24)
        else:
            page.insert_text((40,80),'Semakan dokumen 97531',fontsize=28)
            page.insert_text((40,160),'Maklumat peribadi disimpan',fontsize=24)
        image=page.get_pixmap(dpi=200).tobytes('png')
    with pdf.open() as doc:
        page=doc.new_page(width=500,height=300);page.insert_image(page.rect,stream=image);doc.save(path)


@pytest.mark.parametrize('language,chinese',[('msa',False),('eng+msa',False),('chi_sim',True),('eng+chi_sim',True),('eng+msa+chi_sim',True)])
def test_language_models_recognize_local_scans_and_preserve_appearance(tmp_path,language,chinese):
    source=tmp_path/'source.pdf';scan(source,chinese);original=fingerprint(source)
    engine=Engine(tmp_path/'data');opened=engine.open_file({'path':str(source)})
    changed=engine.dispatch({'command':'apply','session':opened['id'],'revision':0,'args':{'operation':'ocr','language':language}})
    with pdf.open(changed['path']) as doc:
        text=doc[0].get_text().replace(' ','')
        assert ('86420' if chinese else '97531') in text
        if chinese:assert '文件' in text and '测试' in text
        else:assert 'Semakan' in text and 'dokumen' in text
    output=tmp_path/'saved.pdf';engine.dispatch({'command':'export','session':opened['id'],'args':{'path':str(output)}})
    with pdfium.PdfDocument(source) as before,pdfium.PdfDocument(output) as after:
        assert before[0].render().to_pil().tobytes()==after[0].render().to_pil().tobytes()
        assert ('86420' if chinese else '97531') in after[0].get_textpage().get_text_range()
    assert fingerprint(source)==original


@pytest.mark.parametrize('language',['fra','eng+eng','eng++msa','../eng','chi_tra'])
def test_unbundled_or_malformed_languages_reject(language):
    with pytest.raises(PDFError,match='Choose'):validate_language(language,tessdata_dir())


def test_missing_model_rejects_and_capabilities_expose_bundled_languages(tmp_path):
    with pytest.raises(PDFError,match='missing'):validate_language('eng+msa',tmp_path)
    engine=Engine(tmp_path/'data');assert engine.dispatch({'command':'capabilities'})['ocr_languages']==['eng','msa','chi_sim']


def test_language_recipe_survives_restart_and_batch_reopen(tmp_path):
    source=tmp_path/'source.pdf';scan(source,True);original=fingerprint(source)
    engine=Engine(tmp_path/'data')
    saved=engine.dispatch({'command':'preset_save','args':{'name':'Chinese and English scans','steps':[{'operation':'ocr','language':'eng+chi_sim','dpi':200}],'export':'pdf'}})
    restarted=Engine(engine.root)
    recipe=next(item for item in restarted.dispatch({'command':'preset_list'}) if item['id']==saved['id'])
    assert recipe['steps'][0]['language']=='eng+chi_sim'
    result=restarted.dispatch({'command':'batch_run','args':{'preset':saved['id'],'paths':[str(source)],'folder':str(tmp_path/'output')}})
    assert result['items'][0]['status']=='done'
    with pdfium.PdfDocument(result['items'][0]['output']) as checked:
        text=checked[0].get_textpage().get_text_range().replace(' ','')
        assert '文件' in text and '86420' in text
    assert fingerprint(source)==original


def test_invalid_language_recipe_rejects_before_persistence(tmp_path):
    engine=Engine(tmp_path/'data')
    with pytest.raises(PDFError,match='Choose'):
        engine.dispatch({'command':'preset_save','args':{'name':'Invalid','steps':[{'operation':'ocr','language':'eng+eng'}]}})
    assert len(engine.dispatch({'command':'preset_list'}))==3
