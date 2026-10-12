"""Standard AcroForm radio groups with explicit parent and appearance states."""
import re
import uuid
import pymupdf as pdf


def pdf_name(value):
    return '/'+''.join(chr(byte) if 33<=byte<=126 and chr(byte) not in '#%()<>[]{}/' else f'#{byte:02X}' for byte in value.encode('utf-8'))


def create_group(doc,page,args):
    from engine import PDFError,valid_rect,rgb
    name=str(args.get('name') or f'choice_{uuid.uuid4().hex[:8]}').strip()
    choices=[line.strip() for line in str(args.get('choices','')).splitlines() if line.strip()]
    if not name or len(name)>120 or any(widget.field_name==name for current in doc for widget in current.widgets() or []):
        raise PDFError('Choose a new radio group name of 1-120 characters.')
    if not 2<=len(choices)<=20 or len(set(choices))!=len(choices):raise PDFError('Enter 2-20 distinct radio option labels.')
    if any(len(label)>100 or any(ord(char)>255 for char in label) for label in choices):raise PDFError('Use Latin option labels of up to 100 characters.')
    visual=pdf.Rect(args['rect']);valid_rect(visual,page)
    size=float(args.get('size',12))
    row=visual.height/len(choices);button=min(18,row-4)
    if not 6<=size<=30 or button<10 or visual.width<button+30:raise PDFError('Choose a larger radio group rectangle or a size of 6-30 points.')
    children=[]
    for index,label in enumerate(choices):
        top=visual.y0+index*row+(row-button)/2
        rect=pdf.Rect(visual.x0,top,visual.x0+button,top+button)
        widget=pdf.Widget();widget.field_name=f'{name}_temporary_{uuid.uuid4().hex[:8]}';widget.field_type=pdf.PDF_WIDGET_TYPE_RADIOBUTTON
        widget.rect=rect*page.derotation_matrix;widget.field_value=False;widget.border_width=1;widget.border_color=(0,0,0);widget.text_color=rgb(args.get('color'))
        children.append(page.add_widget(widget).xref)
        label_top=visual.y0+index*row+(row-size*1.5)/2
        label_rect=pdf.Rect(visual.x0+button+6,label_top,visual.x1,label_top+size*1.5)
        if page.insert_textbox(label_rect*page.derotation_matrix,label,fontsize=size,rotate=page.rotation,color=rgb(args.get('color')))<0:
            raise PDFError('An option label does not fit. Enlarge the rectangle or reduce the size.')
    parent=doc.get_new_xref()
    doc.update_object(parent,f'<< /FT /Btn /Ff 32768 /T {pdf.get_pdf_str(name)} /V /Off /Kids [{" ".join(f"{xref} 0 R" for xref in children)}] >>')
    for index,xref in enumerate(children):
        off=doc.xref_get_key(xref,'AP/N/Off')[1];on=doc.xref_get_key(xref,'AP/N/Yes')[1]
        doc.xref_set_key(xref,'AP/N',f'<< /Off {off} /O{index+1} {on} >>')
        for key in ('T','FT','Ff','V'):doc.xref_set_key(xref,key,'null')
        # A widget inherits these entries from its parent. Remove them entirely;
        # PDF.js interprets an explicitly present null /T as a field name.
        doc.update_object(xref,re.sub(r'/(?:T|FT|Ff|V)\s+null\b','',doc.xref_object(xref)))
        doc.xref_set_key(xref,'Parent',f'{parent} 0 R');doc.xref_set_key(xref,'TU',pdf.get_pdf_str(choices[index]))
    catalog=doc.pdf_catalog();kind,value=doc.xref_get_key(catalog,'AcroForm')
    owner=int(value.split()[0]) if kind=='xref' else catalog
    key='Fields' if kind=='xref' else 'AcroForm/Fields'
    kind,value=doc.xref_get_key(owner,key)
    if kind=='xref':value=doc.xref_object(int(value.split()[0]))
    if not re.fullmatch(r'\[\s*(?:\d+\s+\d+\s+R\s*)*\]',value.strip()):raise PDFError('This form field catalog needs further compatibility support.')
    refs=[(int(number),int(generation)) for number,generation in re.findall(r'(\d+)\s+(\d+)\s+R',value)]
    refs=[reference for reference in refs if reference[0] not in children]+[(parent,0)]
    doc.xref_set_key(owner,key,'['+' '.join(f'{xref} {generation} R' for xref,generation in refs)+']')


def fill_groups(doc,values):
    from engine import PDFError
    groups={}
    for page in doc:
        for widget in page.widgets() or []:
            if widget.field_type!=pdf.PDF_WIDGET_TYPE_RADIOBUTTON:continue
            kind,reference=doc.xref_get_key(widget.xref,'Parent')
            parent=int(reference.split()[0]) if kind=='xref' else widget.xref
            group=groups.setdefault(parent,{'widgets':[],'requested':[]})
            group['widgets'].append((widget.xref,widget.on_state(),widget.field_flags,widget.field_name))
            if str(widget.xref) in values:group['requested'].append(str(values[str(widget.xref)]))
    handled=set()
    for parent,group in groups.items():
        if not group['requested']:continue
        if len({item[3] for item in group['widgets']})!=1:raise PDFError('This radio field hierarchy needs further compatibility support.')
        states={item[1] for item in group['widgets']}
        requested=set(group['requested'])-{'Off'}
        if len(requested)>1 or any(value not in states for value in requested):raise PDFError('Choose one valid option per radio group.')
        selected=next(iter(requested),'Off')
        kind,current=doc.xref_get_key(parent,'V')
        if kind=='string':current=pdf_name(current)
        elif kind=='null':current='/Off'
        if selected=='Off' and current!='/Off' and any(flags & pdf.PDF_BTN_FIELD_IS_NO_TOGGLE_TO_OFF for _,_,flags,_ in group['widgets']):
            raise PDFError('This radio group requires an option to remain selected.')
        if any(flags & pdf.PDF_FIELD_IS_READ_ONLY for _,_,flags,_ in group['widgets']) and current!=pdf_name(selected):
            raise PDFError('This radio group is read-only.')
        doc.xref_set_key(parent,'V',pdf_name(selected))
        for xref,state,_,_ in group['widgets']:
            doc.xref_set_key(xref,'AS',pdf_name(state) if state==selected else '/Off');handled.add(str(xref))
    return handled
