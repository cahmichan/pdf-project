"""Split a working PDF into separate, independently validated output copies."""
from pathlib import Path
import uuid
import pymupdf as pdf
from engine import PDFError, pages_arg
from workflows import write_json


def split(engine,session,args):
    with pdf.open(engine.current(session)) as doc:
        count=len(doc)
        if doc.get_sigflags()>0 and not args.get('allow_signature_changes'):
            raise PDFError('Splitting creates rewritten copies and may invalidate signatures. Confirm before exporting.')
    mode=args.get('mode','individual')
    if mode=='individual':groups=[[number+1] for number in range(count)]
    elif mode=='every':
        size=args.get('size')
        if isinstance(size,bool) or not isinstance(size,int) or size<1:
            raise PDFError('Choose a positive whole number of pages per file.')
        groups=[list(range(start+1,min(start+size,count)+1)) for start in range(0,count,size)]
    elif mode=='ranges':
        parts=str(args.get('ranges','')).split(';')
        if any(not part.strip() for part in parts):raise PDFError('Separate non-empty page groups with semicolons, such as 1-3;4-6;7,9.')
        groups=[[number+1 for number in pages_arg(part.strip(),count)] for part in parts]
    else:raise PDFError('Choose individual pages, pages per file, or custom page groups.')
    folder=Path(args['folder']).resolve()
    # Validate every group and signature permission before creating any outputs.
    folder.mkdir(parents=True,exist_ok=True)
    identifier=uuid.uuid4().hex;jobs=engine.root/'jobs';jobs.mkdir(exist_ok=True)
    result={'id':identifier,'preset':'Split PDF','status':'running','revision':session['revision'],
            'manifest':str(folder/f'Folio-split-{identifier}.json'),
            'items':[{'source':session['name'],'pages':group,'status':'pending'} for group in groups]}
    def persist():
        write_json(jobs/(identifier+'.json'),result);write_json(Path(result['manifest']),result)
    persist()
    for index,item in enumerate(result['items']):
        engine.progress(index/len(groups),f'Splitting PDF: file {index+1}/{len(groups)}')
        item['status']='running';persist()
        destination=folder/f'{Path(session["name"]).stem}-part-{index+1:03}-{identifier[:12]}.pdf'
        try:
            output=engine.export(session,{'path':str(destination),'mode':'extract','pages':item['pages'],
                                        'allow_signature_changes':args.get('allow_signature_changes',False)})
            item.update(status='done',output=output['path'],bytes=output['bytes'])
        except Exception as error:item.update(status='failed',error=str(error))
        persist()
    result['status']='finished';persist();return result
