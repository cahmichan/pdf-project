"""Read-only embedded font resources for local live editing."""
import base64
import hashlib
import re


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
        if entry:
            _,extension,_,content=doc.extract_font(entry[0])
            if content:
                if extension not in ('ttf','otf','woff','woff2'):
                    result['reason']='This embedded font format needs further preview support.'
                elif len(content)>8_000_000 or total+len(content)>12_000_000:
                    result['reason']='This font exceeds the live preview memory limit.'
                else:
                    total+=len(content);result.update(status='embedded',format=extension,sha256=hashlib.sha256(content).hexdigest(),data=base64.b64encode(content).decode('ascii'))
        output.append(result)
    return {'fonts':output}
