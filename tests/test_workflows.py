from pathlib import Path
import json
import sys
import pytest
import pymupdf as pdf
import pypdfium2 as pdfium
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'worker'))
from engine import Engine, fingerprint


def test_saved_recipe_batch_continues_failures_and_preserves_sources(tmp_path):
    source=tmp_path/'source.pdf';doc=pdf.open();page=doc.new_page();page.insert_text((40,60),'Batch reference 13579');doc.save(source);doc.close()
    broken=tmp_path/'invalid.pdf';broken.write_bytes(b'not a PDF')
    original=fingerprint(source);engine=Engine(tmp_path/'working')
    saved=engine.dispatch({'command':'preset_save','args':{'name':'My handouts','steps':[{'operation':'page_numbers','pages':'all'}],'export':'pdf'}})
    restarted=Engine(engine.root)
    assert any(item['id']==saved['id'] for item in restarted.dispatch({'command':'preset_list'}))
    output=tmp_path/'output';result=restarted.dispatch({'command':'batch_run','args':{'preset':saved['id'],'paths':[str(broken),str(source),str(source)],'folder':str(output)}})
    assert [item['status'] for item in result['items']]==['failed','done','done']
    assert len({item['output'] for item in result['items'][1:]})==2
    assert fingerprint(source)==original
    for item in result['items'][1:]:
        with pdfium.PdfDocument(item['output']) as independent:
            assert 'Batch reference 13579' in independent[0].get_textpage().get_text_range()
    receipt=json.loads(Path(result['manifest']).read_text(encoding='utf-8'))
    assert receipt['status']=='finished'
    assert restarted.dispatch({'command':'batch_history'})[0]['id']==result['id']
    restarted.dispatch({'command':'preset_delete','args':{'id':saved['id']}})
    assert len(restarted.dispatch({'command':'preset_list'}))==3


def test_recipe_rejects_active_file_arguments_and_reports_interrupted_job(tmp_path):
    engine=Engine(tmp_path/'working')
    with pytest.raises(ValueError,match='unsupported settings'):
        engine.dispatch({'command':'preset_save','args':{'name':'Invalid','steps':[{'operation':'rotate','path':'arbitrary.exe'}]}})
    jobs=engine.root/'jobs';jobs.mkdir()
    (jobs/'interrupted.json').write_text(json.dumps({'id':'test','status':'running','items':[{'source':'source.pdf','status':'done'}]}))
    assert engine.dispatch({'command':'batch_history'})[0]['status']=='interrupted'


def test_batch_skips_signature_fields_and_preserves_plain_copy(tmp_path):
    source=tmp_path/'signature-fields.pdf';doc=pdf.open();page=doc.new_page()
    field=pdf.Widget();field.field_type=pdf.PDF_WIDGET_TYPE_SIGNATURE;field.field_name='Signature';field.rect=pdf.Rect(40,40,230,80);page.add_widget(field)
    doc.save(source);doc.close();before=fingerprint(source);engine=Engine(tmp_path/'working')
    opened=engine.dispatch({'command':'open','args':{'path':str(source)}})
    with pytest.raises(Exception,match='signature fields'):
        engine.dispatch({'command':'export','session':opened['id'],'args':{'path':str(tmp_path/'rewritten.pdf'),'mode':'compress'}})
    result=engine.dispatch({'command':'batch_run','args':{'preset':'smaller','paths':[str(source)],'folder':str(tmp_path/'outputs')}})
    assert result['items'][0]['status']=='failed' and 'signature' in result['items'][0]['error']
    saved=engine.dispatch({'command':'export','session':opened['id'],'args':{'path':str(tmp_path/'exact.pdf')}})
    assert Path(saved['path']).read_bytes()==source.read_bytes() and fingerprint(source)==before
