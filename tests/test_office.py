"""Real free-runtime interoperability checks; skipped when runtime is absent."""
from pathlib import Path
import sys
import zipfile
import pytest
import pypdfium2 as pdfium
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'worker'))
from engine import Engine, fingerprint
from office import locate, reject_active_links


@pytest.mark.parametrize('format',['docx','xlsx','pptx'])
def test_import_office_to_searchable_pdf(tmp_path,format):
    if locate(tmp_path) is None:pytest.skip('Optional free LibreOffice runtime is not available')
    source=tmp_path/f'Office sample with spaces.{format}'
    text='Office interoperability 31415'
    if format=='docx':
        from docx import Document
        document=Document();document.add_heading(text,0);document.add_paragraph('Converted locally without Microsoft Office.');document.save(source)
    elif format=='xlsx':
        from openpyxl import Workbook
        document=Workbook();document.active['A1']=text;document.active.column_dimensions['A'].width=45;document.save(source)
    else:
        from pptx import Presentation
        from pptx.util import Inches
        document=Presentation();slide=document.slides.add_slide(document.slide_layouts[6]);slide.shapes.add_textbox(Inches(1),Inches(1),Inches(8),Inches(1)).text=text;document.save(source)
    before=fingerprint(source);engine=Engine(tmp_path/'sessions')
    session=engine.dispatch({'command':'import_office','args':{'path':str(source)}})
    assert session['dirty'] and session['name'].endswith('.pdf')
    assert fingerprint(source)==before
    with pdfium.PdfDocument(session['path']) as independent:
        assert len(independent)>=1
        assert '31415' in ''.join(page.get_textpage().get_text_range() for page in independent)
        assert independent[0].render(scale=1).width>0
    output=tmp_path/'converted.pdf'
    engine.dispatch({'command':'export','session':session['id'],'args':{'path':str(output)}})
    assert output.is_file() and fingerprint(source)==before


def test_office_external_image_is_rejected(tmp_path):
    source=tmp_path/'external.docx'
    relationships='''<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image" Target="https://example.invalid/image.png" TargetMode="External"/></Relationships>'''
    with zipfile.ZipFile(source,'w') as archive:archive.writestr('word/_rels/document.xml.rels',relationships)
    with pytest.raises(ValueError,match='external linked content'):reject_active_links(source)
