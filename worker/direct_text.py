"""Direct paragraph editing with source-font reuse and measured placement."""
import math
import re
import uuid
import pymupdf as pdf


def paragraphs(page):
    result=[]
    for index,block in enumerate(page.get_text('dict')['blocks']):
        if block['type']!=0 or not block.get('lines'):continue
        spans=[span for line in block['lines'] for span in line['spans']]
        if not spans:continue
        first=spans[0];raw=pdf.Rect(block['bbox'])
        result.append({'id':index,'text':'\n'.join(''.join(span['text'] for span in line['spans']) for line in block['lines']),
                       'rect':list(raw*page.rotation_matrix),'raw_rect':list(raw),'size':first['size'],
                       'font':first['font'],'flags':first['flags'],'color':'#'+format(first['color'],'06x'),
                       'rotation':page.rotation,'horizontal':all(abs(line['dir'][0]-1)<.01 and abs(line['dir'][1])<.01 for line in block['lines']),
                       'origin':list(first['origin']),'mixed_styles':len({(span['font'],round(span['size'],2),span['color']) for span in spans})>1})
    return result


def font_choice(doc,page,args,original,text):
    from engine import PDFError
    family=args.get('font','original' if original else 'helv')
    if family=='original':
        if original['mixed_styles']:raise PDFError('This paragraph has mixed fonts or styles. Choose one replacement font explicitly before applying.')
        name=original['font'];clean=lambda value:re.sub(r'^[A-Z]{6}\+','',value).lower().replace('-','').replace(' ','')
        for entry in page.get_fonts(full=True):
            if entry[0] and clean(entry[3])==clean(name):
                buffer=doc.extract_font(entry[0])[3]
                if buffer:
                    font=pdf.Font(fontbuffer=buffer)
                    if any(not font.has_glyph(ord(char)) for char in text if not char.isspace()):
                        raise PDFError('The original embedded font lacks a replacement character. Choose another font.')
                    return font,'FolioEdit'+uuid.uuid4().hex[:8],buffer
        aliases={'helvetica':'helv','arial':'helv','arialmt':'helv','helveticabold':'hebo','arialboldmt':'hebo','helveticaoblique':'heit','helveticaboldoblique':'hebi',
                 'timesroman':'tiro','timesnewromanpsmt':'tiro','timesbold':'tibo','timesitalic':'tiit','timesbolditalic':'tibi',
                 'courier':'cour','courierbold':'cobo','courieroblique':'coit','courierboldoblique':'cobi'}
        family=aliases.get(clean(name))
        if not family:raise PDFError('The original font is unavailable for editing. Choose a replacement font.')
    if family not in ('helv','hebo','heit','hebi','tiro','tibo','tiit','tibi','cour','cobo','coit','cobi'):
        raise PDFError('Choose a supported text font.')
    if any(ord(char)>255 for char in text):raise PDFError('This replacement font supports Latin text. Use an original embedded font with the required characters.')
    return pdf.Font(family),family,None


def edit(doc,page,args):
    from engine import PDFError,rgb
    items=paragraphs(page);adding=args.get('operation')=='insert_text'
    original=None
    if not adding:
        expected=str(args.get('expected',''));anchor=pdf.Rect(args.get('source_rect',[0,0,0,0]))
        matches=[item for item in items if item['text']==expected and max(abs(a-b) for a,b in zip(item['raw_rect'],anchor))<1]
        if len(matches)!=1:raise PDFError('The selected text changed. Select it again before editing.')
        original=matches[0]
        if not original['horizontal']:raise PDFError('Text with an angled baseline needs further editing support. Add new text or choose a horizontal paragraph.')
    text=str(args.get('text','')).replace('\r\n','\n').replace('\r','\n').replace('\t','    ')
    if adding and not text.strip():raise PDFError('Type text at the insertion point before applying.')
    if len(text)>20000:raise PDFError('Edit at most 20,000 characters in one paragraph.')
    size=float(args.get('size',original['size'] if original else 12))
    if not math.isfinite(size) or not 1<=size<=300:raise PDFError('Choose a font size from 1 to 300 points.')
    styled=None
    if original and original['mixed_styles'] and text and args.get('font','original')=='original':
        from styled_text import StyledText
        styled=StyledText(doc,page,original,text,args)
    font,fontname,buffer=font_choice(doc,page,{**args,'font':'helv'} if not text else args,{**original,'mixed_styles':False} if styled else original,text if not styled else '')
    bounds=page.rect*page.derotation_matrix
    if adding:
        point=args.get('point',[])
        if len(point)!=2 or not all(isinstance(v,(int,float)) and math.isfinite(v) for v in point):raise PDFError('Click a valid insertion position on the page.')
        visual=pdf.Point(point)
        if not page.rect.contains(visual):raise PDFError('Click inside the page to add text.')
        region=pdf.Rect(visual.x,visual.y,page.rect.x1-2,page.rect.y1-2)
        obstacles=[pdf.Rect(item['rect']) for item in items]
        rotation=page.rotation
    else:
        origin=original['origin'];region=pdf.Rect(original['raw_rect'][0],origin[1]-font.ascender*size,bounds.x1-2,bounds.y1-2)
        if styled:region.y0=styled.top
        obstacles=[pdf.Rect(item['raw_rect']) for item in items if item['id']!=original['id']]
        rotation=0
        old=pdf.Rect(original['raw_rect'])
        if any(old.intersects(pdf.Rect(image['bbox'])) for image in page.get_image_info()):raise PDFError('This text overlaps a scan or image. Scan reconstruction requires a separate workflow.')
        if any(old.intersects(other) for other in obstacles):raise PDFError('Overlapping text needs further editing support. The original paragraph has not been changed.')
    # Let typing grow automatically into free space, bounded by neighboring text.
    for other in obstacles:
        if other.x0>region.x0 and other.y0<region.y0+size*1.4 and other.y1>region.y0:region.x1=min(region.x1,other.x0-2)
        if other.y0>region.y0 and other.x1>region.x0 and other.x0<region.x1:region.y1=min(region.y1,other.y0-2)
    raw=region*page.derotation_matrix if adding else region
    if raw.is_empty or not bounds.contains(raw):raise PDFError('There is no room for text here. Choose another position or reduce the font size.')
    color=rgb(args.get('color',original['color'] if original else '#253653'))
    def place(target):
        if styled:return styled.place(target,raw)
        if buffer:target.insert_font(fontname=fontname,fontbuffer=buffer)
        return target.insert_textbox(raw,text,fontname=fontname,fontsize=size,color=color,rotate=rotation,lineheight=1.2)
    with pdf.open() as scratch:
        trial=scratch.new_page(width=bounds.width,height=bounds.height)
        if place(trial)<0:raise PDFError('The text would run beyond the page or into neighboring content. Shorten it, reduce the size or use a different position.')
        painted=[pdf.Rect(block['bbox']) for block in trial.get_text('dict')['blocks'] if block['type']==0]
        raw_obstacles=[other*page.derotation_matrix for other in obstacles] if adding else obstacles
        if any(painted_rect.intersects(other) for painted_rect in painted for other in raw_obstacles):
            raise PDFError('The text would overlap another paragraph. Choose another position or reduce the size.')
    if original:
        page.add_redact_annot(pdf.Rect(original['raw_rect']),fill=False)
        page.apply_redactions(images=0,graphics=0,text=0)
    if place(page)<0:raise PDFError('The text could not be placed. The working revision was not changed.')
