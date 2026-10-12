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
# Four synthetic pages exercise every on-page control at each rotation.
doc=pdf.open()
for rotation in (0,90,180,270):
    page=doc.new_page(width=400,height=500);page.set_cropbox(pdf.Rect(20,30,380,470));page.set_rotation(rotation)
    specs=[('Name',pdf.PDF_WIDGET_TYPE_TEXT,[40,40,180,70],'Old',0),('Notes',pdf.PDF_WIDGET_TYPE_TEXT,[40,100,260,155],'Line one',pdf.PDF_TX_FIELD_IS_MULTILINE),('Consent',pdf.PDF_WIDGET_TYPE_CHECKBOX,[40,190,60,210],False,0),('Category',pdf.PDF_WIDGET_TYPE_COMBOBOX,[40,240,170,270],'First',0),('Selection',pdf.PDF_WIDGET_TYPE_LISTBOX,[200,240,320,300],'First',0),('Locked',pdf.PDF_WIDGET_TYPE_TEXT,[40,300,180,330],'Fixed',pdf.PDF_FIELD_IS_READ_ONLY)]
    for name,kind,rect,value,flags in specs:
        field=pdf.Widget();field.field_name=f'{name} {rotation}';field.field_type=kind;field.rect=pdf.Rect(rect);field.field_value=value;field.field_flags=flags
        if name=='Name':field.text_maxlen=8
        if kind in (pdf.PDF_WIDGET_TYPE_COMBOBOX,pdf.PDF_WIDGET_TYPE_LISTBOX):field.choice_values=['First','Second']
        page.add_widget(field)
doc.save(folder/'forms.pdf');doc.close()
doc=pdf.open();page=doc.new_page(width=500,height=700)
for index,name in enumerate(('__proto__','constructor','toString')):
    field=pdf.Widget();field.field_name=name;field.field_type=pdf.PDF_WIDGET_TYPE_TEXT;field.rect=pdf.Rect(40,80+index*90,400,115+index*90);field.field_value='Initial';field.text_fontsize=14;page.add_widget(field)
doc.save(folder/'unusual-fields.pdf');doc.close()

# Phone-like perspective photo for the local document scanner.
import cv2
import numpy as np
from PIL import Image
photo_page=np.full((700,500,3),245,np.uint8)
cv2.putText(photo_page,"SCAN TEST",(40,90),cv2.FONT_HERSHEY_SIMPLEX,1.4,(20,20,20),3)
for y in range(140,600,45):cv2.line(photo_page,(40,y),(440,y),(60,60,60),3)
photo_transform=cv2.getPerspectiveTransform(np.float32([[0,0],[499,0],[499,699],[0,699]]),np.float32([[130,100],[700,145],[650,850],[90,790]]))
Image.fromarray(cv2.warpPerspective(photo_page,photo_transform,(800,950),borderValue=(35,50,65))).save(folder/"scan-photo.png")

# Synthetic video input; native tests never activate a real camera.
camera_frame=cv2.cvtColor(cv2.imread(str(folder/"scan-photo.png")),cv2.COLOR_BGR2YUV_I420).tobytes()
(folder/"camera.y4m").write_bytes(b"YUV4MPEG2 W800 H950 F30:1 Ip A1:1 C420jpeg\n"+b"FRAME\n"+camera_frame)

# Mixed font/size/color paragraph for direct styled editing.
mixed=pdf.open();mixed_page=mixed.new_page(width=500,height=700);mixed_x=40
for mixed_text,mixed_font,mixed_size,mixed_color in [("Total: ","helv",14,(0,0,0)),("$100","hebo",18,(.8,0,0)),(" paid","tiit",14,(0,.3,0))]:
 mixed_page.insert_text((mixed_x,80),mixed_text,fontname=mixed_font,fontsize=mixed_size,color=mixed_color);mixed_x+=pdf.get_text_length(mixed_text,fontname=mixed_font,fontsize=mixed_size)
mixed_page.insert_text((40,300),"Keep neighbor",fontsize=12);mixed.save(folder/"mixed-styles.pdf");mixed.close()

# Digital heading/footer plus a rasterized invoice region.
ocr_image_doc=pdf.open();ocr_image_page=ocr_image_doc.new_page(width=400,height=250);ocr_image_page.insert_text((35,75),"Scanned invoice 24680",fontsize=24);ocr_image_page.insert_text((35,145),"Mixed content recognition",fontsize=20)
ocr_image=ocr_image_page.get_pixmap(dpi=200).tobytes("png");ocr_image_doc.close()
ocr_mixed=pdf.open();ocr_mixed_page=ocr_mixed.new_page(width=500,height=700);ocr_mixed_page.insert_text((35,70),"Digital heading 13579",fontsize=20);ocr_mixed_page.insert_image(pdf.Rect(30,140,430,390),stream=ocr_image);ocr_mixed_page.insert_text((35,500),"Digital footer remains",fontsize=16);ocr_mixed.save(folder/"mixed-ocr.pdf");ocr_mixed.close()
