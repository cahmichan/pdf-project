from pathlib import Path
import sys
import pytest
import pymupdf as pdf
import pypdfium2 as pdfium
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'worker'))
from engine import Engine, fingerprint, PDFError
from archival import locate, parse_report


@pytest.mark.parametrize('rotation',[0,90,270])
def test_archival_conformance_visible_pages_text_and_original(tmp_path,rotation):
    if locate(tmp_path) is None:pytest.skip('Optional archival runtime is absent')
    source=tmp_path/'archive source.pdf'
    doc=pdf.open();page=doc.new_page(width=400,height=500)
    page.insert_text((40,80),'Archival fixture 12345',fontsize=18)
    page.draw_rect(pdf.Rect(40,100,200,130),color=(1,0,0),fill=(.7,.9,.8),fill_opacity=.5)
    widget=pdf.Widget();widget.rect=pdf.Rect(40,160,250,200);widget.field_name='FullName'
    widget.field_type=pdf.PDF_WIDGET_TYPE_TEXT;widget.field_value='Archive Person';page.add_widget(widget)
    page.insert_link({'kind':pdf.LINK_URI,'from':pdf.Rect(40,250,200,280),'uri':'https://example.invalid/'})
    page.set_cropbox(pdf.Rect(20,30,380,470));page.set_rotation(rotation)
    doc.embfile_add('fixture.txt',b'Synthetic attachment');doc.save(source);doc.close()
    baseline=fingerprint(source);engine=Engine(tmp_path/'data')
    opened=engine.dispatch({'command':'open','args':{'path':str(source)}})
    destination=tmp_path/'archive.pdf'
    result=engine.dispatch({'command':'export','session':opened['id'],'args':{'path':str(destination),'mode':'pdfa_2b'}})
    validation=result['validation']
    assert validation['compliant'] and validation['failed_rules']==0 and validation['passed_rules']>100
    assert 'PDF/A-2b' in validation['profile']
    report=tmp_path/'report.xml'
    engine.dispatch({'command':'save_validation_report','session':opened['id'],'args':{'path':str(report),'report':validation['report']}})
    assert parse_report(report.read_text(encoding='utf-8'))['compliant']
    with pdfium.PdfDocument(str(destination)) as independent:
        assert len(independent)==1
        text=independent[0].get_textpage().get_text_range()
        assert '12345' in text and 'Archive Person' in text
        image=independent[0].render(scale=1).to_pil()
        assert image.size==((440,360) if rotation else (360,440))
    with pdf.open(destination) as converted:
        page=converted[0]
        assert not list(page.widgets() or []) and not page.get_links() and not converted.embfile_names()
    assert fingerprint(source)==baseline
    assert engine.dispatch({'command':'info','session':opened['id']})['revision']==0
    plain=engine.dispatch({'command':'inspect_pdfa','session':opened['id']})
    assert not plain['compliant'] and plain['failed_rules']>0
    with pytest.raises(PDFError):
        engine.dispatch({'command':'save_validation_report','session':opened['id'],'args':{'path':str(tmp_path/'forged.xml'),'report':str(source)}})


def test_validator_rejects_incomplete_report():
    incomplete='<report><validationReport isCompliant="true" jobEndStatus="failed"><details passedRules="3" failedRules="0"/></validationReport></report>'
    assert not parse_report(incomplete)['compliant']
    with pytest.raises(ValueError):parse_report('<report/>')

def test_archival_validation_failure_preserves_previous_output(tmp_path,monkeypatch):
    if locate(tmp_path) is None:pytest.skip('Optional archival runtime is absent')
    import archival
    source=tmp_path/'source.pdf';document=pdf.open();document.new_page().insert_text((40,60),'Failure fixture');document.save(source);document.close()
    previous=tmp_path/'existing.pdf';previous.write_bytes(source.read_bytes());baseline=fingerprint(previous)
    engine=Engine(tmp_path/'data');session=engine.dispatch({'command':'open','args':{'path':str(source)}})
    monkeypatch.setattr(archival,'validate',lambda *args:{'compliant':False,'failed_rules':1,'statement':'Synthetic conformance failure'})
    with pytest.raises(ValueError,match='failed PDF/A-2b'):
        engine.dispatch({'command':'export','session':session['id'],'args':{'path':str(previous),'mode':'pdfa_2b','overwrite':True}})
    assert fingerprint(previous)==baseline and fingerprint(source)==baseline
    assert not list(tmp_path.glob('.folio-*'))
