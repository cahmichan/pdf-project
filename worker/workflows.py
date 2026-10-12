"""Persisted presets and source-preserving batch jobs."""
import json
import os
from pathlib import Path
import uuid

OPERATIONS={'rotate','crop','page_numbers','watermark','ocr','metadata','flatten_forms'}
EXPORTS={'pdf','compress','compress_screen','compress_print','txt','markdown','docx','pptx','pptx_images','xlsx'}
BUILTINS=[
    {'id':'searchable','name':'Searchable scans','steps':[{'operation':'ocr','pages':'all'}],'export':'pdf','builtin':True},
    {'id':'handout','name':'Numbered handout','steps':[{'operation':'page_numbers','pages':'all'}],'export':'pdf','builtin':True},
    {'id':'smaller','name':'Smaller PDF for screens','steps':[],'export':'compress_screen','builtin':True},
]


def write_json(path: Path, value):
    temporary=path.with_suffix('.pending.json')
    temporary.write_text(json.dumps(value,indent=2,ensure_ascii=False),encoding='utf-8');os.replace(temporary,path)


def valid_id(identifier):
    value=str(uuid.UUID(identifier))
    if value!=identifier:raise ValueError('Invalid preset identifier.')
    return value


def list_presets(root: Path):
    folder=root/'presets';folder.mkdir(exist_ok=True)
    result=list(BUILTINS)
    for path in sorted(folder.glob('*.json')):
        try:result.append(json.loads(path.read_text(encoding='utf-8')))
        except (ValueError,OSError):continue
    return result


def validate(args):
    name=str(args.get('name','')).strip()
    if not name or len(name)>80:raise ValueError('Give the preset a name of 1-80 characters.')
    steps=args.get('steps',[])
    if not isinstance(steps,list) or len(steps)>20:raise ValueError('Choose up to 20 steps.')
    for step in steps:
        if not isinstance(step,dict) or step.get('operation') not in OPERATIONS:raise ValueError('Unsupported preset step.')
        if any(key not in ('operation','pages','degrees','margin','text','size','color','start','opacity','title','author','subject','keywords','language','dpi','ocr_mode','margins','crop_mode','number_format','position','align','inset','edge') for key in step):
            raise ValueError('Preset contains unsupported settings.')
        if step.get('operation')=='ocr' and step.get('ocr_mode','missing') not in ('missing','skip_text'):raise ValueError('Unsupported OCR mode.')
    if args.get('export','pdf') not in EXPORTS:raise ValueError('Unsupported preset export format.')
    return {'id':str(uuid.uuid4()),'name':name,'steps':steps,'export':args.get('export','pdf'),'builtin':False}


def save_preset(root:Path,args):
    preset=validate(args);folder=root/'presets';folder.mkdir(exist_ok=True)
    write_json(folder/(preset['id']+'.json'),preset);return preset


def delete_preset(root:Path,identifier):
    path=root/'presets'/(valid_id(identifier)+'.json')
    path.unlink(missing_ok=True)


def run_batch(engine,args):
    preset=next((item for item in list_presets(engine.root) if item['id']==args['preset']),None)
    if preset is None:raise ValueError('Preset was not found.')
    # Validate stored presets before execution, including manual file edits.
    validate(preset)
    inputs=args.get('paths',[])
    if not isinstance(inputs,list) or not 1<=len(inputs)<=100:raise ValueError('Choose 1-100 input PDFs.')
    folder=Path(args['folder']).resolve();folder.mkdir(parents=True,exist_ok=True)
    identifier=uuid.uuid4().hex
    jobs=engine.root/'jobs';jobs.mkdir(exist_ok=True)
    result={'id':identifier,'preset':preset['name'],'status':'running','items':[{'source':str(Path(path).resolve()),'status':'pending'} for path in inputs],'manifest':str(folder/f'Folio-batch-{identifier}.json')}
    def persist():
        write_json(jobs/(identifier+'.json'),result);write_json(Path(result['manifest']),result)
    persist()
    for index,item in enumerate(result['items']):
        engine.progress(index/len(inputs),f'Batch {index+1}/{len(inputs)}: {Path(item["source"]).name}')
        item['status']='running';persist()
        try:
            opened=engine.open_file({'path':item['source']});session=engine.session(opened['id'])
            if opened['signature_fields'] and (preset['steps'] or preset['export'] in ('compress','compress_screen','compress_print')):
                raise ValueError('PDF has signature fields. Review and export this file individually before batch processing.')
            for step in preset['steps']:
                engine.apply(session,step)
            mode=preset['export'];extension={'txt':'.txt','markdown':'.md','docx':'.docx','pptx':'.pptx','pptx_images':'.pptx','xlsx':'.xlsx'}.get(mode,'.pdf')
            destination=folder/(Path(item['source']).stem+'-folio-'+uuid.uuid4().hex[:12]+extension)
            exported=engine.export(session,{'path':str(destination),'mode':mode})
            item.update(status='done',output=exported['path'],bytes=exported['bytes'],session=opened['id'])
        except Exception as error:
            item.update(status='failed',error=str(error))
        persist()
    result['status']='finished';persist();return result


def history(root:Path):
    result=[]
    for path in sorted((root/'jobs').glob('*.json'),key=lambda path:path.stat().st_mtime,reverse=True)[:20]:
        try:
            job=json.loads(path.read_text(encoding='utf-8'))
            if job['status']=='running':job['status']='interrupted'
            result.append(job)
        except (ValueError,OSError,KeyError):continue
    return result
