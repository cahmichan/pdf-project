"""Page geometry tools expressed in the coordinates the reader displays."""
import math
import pymupdf as pdf


def crop_page(page,args):
    from engine import PDFError
    mode=args.get('crop_mode','margins')
    if mode=='reset':
        media=page.mediabox
        # CropBox's y axis is normalized even when MediaBox's origin is not zero.
        page.set_cropbox(pdf.Rect(media.x0,0,media.x1,media.height))
        return
    if mode=='selection':
        values=args.get('rect',[])
        if not isinstance(values,(list,tuple)) or len(values)!=4:
            raise PDFError('Draw a crop rectangle on the current page.')
        values=[float(value) for value in values]
        if not all(math.isfinite(value) for value in values):raise PDFError('Crop coordinates must be finite.')
        rect=pdf.Rect(values)
    elif mode=='margins':
        margins=args.get('margins')
        if margins is None:
            value=float(args.get('margin',20));margins=dict.fromkeys(('left','top','right','bottom'),value)
        if not isinstance(margins,dict) or set(margins)!= {'left','top','right','bottom'}:
            raise PDFError('Provide all four crop margins.')
        margins={key:float(value) for key,value in margins.items()}
        if any(not math.isfinite(value) or value<0 for value in margins.values()):
            raise PDFError('Crop margins must be finite and non-negative.')
        rect=pdf.Rect(margins['left'],margins['top'],page.rect.width-margins['right'],page.rect.height-margins['bottom'])
    else:raise PDFError('Choose margins, a crop selection, or reset.')
    if rect.is_empty or not page.rect.contains(rect):raise PDFError('The crop must retain a non-empty area inside the page.')
    relative=rect*page.derotation_matrix
    origin=page.cropbox_position
    page.set_cropbox(pdf.Rect(relative.x0+origin.x,relative.y0+origin.y,relative.x1+origin.x,relative.y1+origin.y))


def decorate_page(page,args,offset,total,pages):
    from engine import PDFError,rgb
    numbering=args['operation']=='page_numbers'
    size=float(args.get('size',11 if numbering else 48))
    opacity=float(args.get('opacity',1 if numbering else .3))
    inset=float(args.get('inset',24));edge=float(args.get('edge',12))
    if not all(math.isfinite(value) for value in (size,opacity,inset,edge)) or not 1<=size<=150 or not 0<=opacity<=1 or inset<0 or edge<0:
        raise PDFError('Choose a size of 1-150 points, opacity of 0-1, and non-negative spacing.')
    if numbering:
        start=args.get('start',1)
        if isinstance(start,bool) or not isinstance(start,int) or start<0:raise PDFError('Starting number must be a non-negative whole number.')
        text=str(args.get('number_format','{n}'))
        for key,value in {'n':start+offset,'total':total,'page':page.number+1,'pages':pages}.items():text=text.replace('{'+key+'}',str(value))
        if '{' in text or '}' in text:raise PDFError('Use {n}, {total}, {page}, or {pages} in the number format.')
    else:text=str(args.get('text','DRAFT'))
    if not text or len(text)>500 or '\n' in text or any(ord(character)>255 for character in text):
        raise PDFError('Use a single line of up to 500 Latin characters.')
    position=args.get('position','bottom' if numbering else 'middle')
    align=args.get('align','center')
    if position not in ('top','middle','bottom') or align not in ('left','center','right'):
        raise PDFError('Choose a supported text position and alignment.')
    height=size*1.5
    y=edge if position=='top' else page.rect.height-edge-height if position=='bottom' else (page.rect.height-height)/2
    rect=pdf.Rect(inset,y,page.rect.width-inset,y+height)
    if rect.is_empty or not page.rect.contains(rect):raise PDFError('Text spacing leaves no usable area on this page.')
    if page.insert_textbox(rect*page.derotation_matrix,text,fontsize=size,align={'left':0,'center':1,'right':2}[align],
                           rotate=page.rotation,color=rgb(args.get('color')),fill_opacity=opacity)<0:
        raise PDFError('Text does not fit. Reduce its size or spacing.')
