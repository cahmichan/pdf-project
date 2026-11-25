"""Read-only embedded font resources for local live editing."""
import base64
import hashlib
import re
import pymupdf as pdf

ALIASES={'helvetica':'helv','arial':'helv','arialmt':'helv','helveticabold':'hebo','arialboldmt':'hebo','helveticaoblique':'heit','helveticaboldoblique':'hebi',
         'timesroman':'tiro','timesnewromanpsmt':'tiro','timesbold':'tibo','timesitalic':'tiit','timesbolditalic':'tibi',
         'courier':'cour','courierbold':'cobo','courieroblique':'coit','courierboldoblique':'cobi','symbol':'symb','zapfdingbats':'zadb'}


def resources(doc,page,args):
    from engine import PDFError
    from direct_text import paragraphs
    names=args.get('fonts',[])
    if not isinstance(names,list) or not 1<=len(names)<=32 or any(not isinstance(name,str) for name in names):
        raise PDFError('Choose 1-32 font names from the current page.')
    requested=list(dict.fromkeys(names));available={run['font']:run['flags'] for block in paragraphs(page) for run in block['runs']}
    if any(name not in available for name in requested):raise PDFError('The requested font is not used on this page.')
    def clean(name):return re.sub(r'^[A-Z]{6}\+','',name).lower().replace('-','').replace(' ','')
    entries=page.get_fonts(full=True);output=[];total=0
    for name in requested:
        result={'name':name,'flags':available[name],'status':'substitute','reason':'No embedded font data is available.'}
        matches=[item for item in entries if item[0] and clean(item[3])==clean(name)]
        entry=matches[0] if len(matches)==1 else None
        if len(matches)>1:result['reason']='Several embedded font resources share this name; preview mapping needs review.'
        content=b'';extension='';status='embedded'
        if entry:_,extension,_,content=doc.extract_font(entry[0])
        if not content and len(matches)<=1 and clean(name) in ALIASES:
            content=pdf.Font(ALIASES[clean(name)]).buffer;extension='cff';status='compatible'
        if content:
            if len(content)>8_000_000:
                result['reason']='This font exceeds the live preview memory limit.'
            else:
                source_hash=hashlib.sha256(content).hexdigest();source_format=extension
                if extension=='cff' or (extension=='cid' and content[:4] not in (b'OTTO',b'\x00\x01\x00\x00',b'true')):
                    try:
                        from cff_preview import convert
                        content=convert(content);extension='otf'
                    except Exception as error:
                        result['reason']='CFF preview conversion needs further mapping support: '+str(error);content=b''
                if content:
                    if extension not in ('ttf','otf','woff','woff2'):result['reason']='This embedded font format needs further preview support.'
                    elif len(content)>8_000_000 or total+len(content)>12_000_000:result['reason']='This font exceeds the live preview memory limit.'
                    else:
                        total+=len(content);result.update(status=status,format=extension,source_format=source_format,source_sha256=source_hash,sha256=hashlib.sha256(content).hexdigest(),data=base64.b64encode(content).decode('ascii'))
        output.append(result)
    return {'fonts':output}
