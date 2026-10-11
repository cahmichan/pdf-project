from pathlib import Path
import pymupdf as pdf
root=Path(__file__).resolve().parents[1]
folder=root/'artifacts'/'fixtures';folder.mkdir(parents=True,exist_ok=True)
doc=pdf.open()
for number in range(3):
    page=doc.new_page(width=500,height=700)
    page.insert_text((45,60),f'Folio sample document - page {number+1}',fontsize=22,color=(.15,.2,.35))
    page.insert_text((45,110),'A synthetic document for local interface testing.',fontsize=12)
    page.insert_text((45,140),'Searchable text, editable content, and an interactive form.',fontsize=12)
    page.draw_line((45,175),(455,175),color=(.7,.75,.85))
    page.insert_text((45,205),'Reference code: SAMPLE-12345',fontsize=12)
    if number==0:
        field=pdf.Widget();field.field_name='Full name';field.field_type=pdf.PDF_WIDGET_TYPE_TEXT;field.rect=pdf.Rect(45,245,300,277);field.field_value='Example Person'
        page.add_widget(field)
doc.set_toc([[1,'Introduction',1],[1,'Second page',2],[1,'Final page',3]])
doc[0].insert_text((45,520),'Go to final page',fontsize=12)
doc[0].insert_link({'kind':pdf.LINK_GOTO,'from':pdf.Rect(45,500,220,535),'page':2,'to':pdf.Point(0,0)})
doc.set_metadata({'title':'Folio synthetic fixture','author':'Local automated verification'})
doc.save(folder/'sample.pdf');doc.close()
original=pdf.open();page=original.new_page(width=500,height=700)
page.insert_text((45,75),'Offline OCR test 67890',fontsize=22)
page.insert_text((45,120),'Searchable after recognition',fontsize=18)
image=page.get_pixmap(dpi=150).tobytes('png');original.close()
for name,count in [('scan.pdf',1),('scan-many.pdf',40)]:
    scan=pdf.open();xref=0
    for number in range(count):
        page=scan.new_page(width=500,height=700)
        xref=page.insert_image(page.rect,stream=image,xref=xref)
    scan.save(folder/name,deflate=True);scan.close()
from docx import Document
office=Document();office.add_heading('Native Office import 31415',0);office.add_paragraph('Synthetic file for free-runtime verification.');office.save(folder/'office.docx')
print(folder/'sample.pdf')
