"""Exercise the packaged executable without a developer Python environment."""
import json
import hashlib
import os
import subprocess
import sys
from pathlib import Path
import pymupdf as pdf
root=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(root/'worker'))
from office import locate
from archival import locate as locate_archival
output=root/'artifacts'/'packaged-smoke';output.mkdir(parents=True,exist_ok=True)
binary=Path(sys.argv[1]) if len(sys.argv)>1 else root/'src-tauri'/'binaries'/'pdf-worker.exe'
office_runtime=locate(output/'data')
archival_runtime=locate_archival(output/'data')
settings={}
if office_runtime:
    (output/'data').mkdir(exist_ok=True)
    settings['office_runtime']=str(office_runtime)
if archival_runtime:
    settings.update({name:str(archival_runtime[name]) for name in ('ghostscript_runtime','java_runtime','verapdf_jar')})
if settings:
    (output/'data').mkdir(exist_ok=True)
    (output/'data'/'settings.json').write_text(json.dumps(settings),encoding='utf-8')
environment=os.environ.copy()
environment.pop('PYTHONHOME',None);environment.pop('PYTHONPATH',None)
environment['PATH']=str(Path(os.environ['SystemRoot'])/'System32')
process=subprocess.Popen([str(binary),'--data-dir',str(output/'data')],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,encoding='utf-8',env=environment,cwd=output)
def command(request):
    process.stdin.write(json.dumps(request)+'\n');process.stdin.flush()
    while True:
        result=json.loads(process.stdout.readline())
        if result.get('event')!='progress':break
    assert result['ok'],result
    return result['result']
try:
    info=command({'command':'open','args':{'path':str(root/'artifacts'/'fixtures'/'sample.pdf')}})
    info=command({'command':'apply','session':info['id'],'revision':info['revision'],'args':{'operation':'add_text','page':1,'rect':[45,320,350,360],'text':'Packaged worker verified','size':12}})
    exported=command({'command':'export','session':info['id'],'args':{'path':str(output/'verified.pdf'),'overwrite':True}})
    word=command({'command':'export','session':info['id'],'args':{'path':str(output/'verified.docx'),'mode':'docx','overwrite':True}})
    with pdf.open(exported['path']) as doc:
        assert 'Packaged worker verified' in doc[0].get_text()
    capabilities=command({'command':'capabilities'})
    assert capabilities['ocr_languages']==['eng']
    scan=command({'command':'open','args':{'path':str(root/'artifacts'/'fixtures'/'scan.pdf')}})
    scan=command({'command':'apply','session':scan['id'],'revision':scan['revision'],'args':{'operation':'ocr'}})
    with pdf.open(scan['path']) as recognized:
        assert '67890' in recognized[0].get_text()
    with binary.open('rb') as stream:binary_hash=hashlib.file_digest(stream,'sha256').hexdigest()
    receipt={'passed':True,'binary':str(binary),'binary_sha256':binary_hash,'engine':capabilities['engine'],'output':exported['path'],'word':word['path'],'developer_python_required':False,'bundled_offline_ocr':True}
    if office_runtime:
        converted=command({'command':'import_office','args':{'path':str(root/'artifacts'/'fixtures'/'office.docx')}})
        with pdf.open(converted['path']) as checked:
            assert '31415' in checked[0].get_text()
        receipt['configured_free_office_import']=True
    preset=command({'command':'preset_save','args':{'name':'Packaged numbered handout','steps':[{'operation':'page_numbers','pages':'all'}],'export':'pdf'}})
    batch=command({'command':'batch_run','args':{'preset':preset['id'],'paths':[str(root/'artifacts'/'fixtures'/'sample.pdf')],'folder':str(output/'batch')}})
    assert batch['items'][0]['status']=='done'
    receipt['saved_preset_batch']=True
    organized=command({'command':'apply','session':info['id'],'revision':info['revision'],'args':{'operation':'reorder','pages':[1,1,3]}})
    with pdf.open(organized['path']) as checked:assert checked.page_xref(0)!=checked.page_xref(1)
    parts=command({'command':'split','session':organized['id'],'revision':organized['revision'],'args':{'mode':'ranges','ranges':'3,1;1,1','folder':str(output/'split')}})
    assert all(item['status']=='done' for item in parts['items'])
    with pdf.open(parts['items'][1]['output']) as checked:assert len(checked)==2 and checked.page_xref(0)!=checked.page_xref(1)
    info=command({'command':'undo','session':organized['id'],'revision':organized['revision']})
    receipt['independent_page_copies_and_split']=True
    import uuid
    identity=output/f'synthetic-{uuid.uuid4().hex}.pfx'
    command({'command':'create_identity','args':{'path':str(identity),'name':'Packaged synthetic identity','password':'Synthetic-smoke-only-123'}})
    signed=command({'command':'sign_copy','session':info['id'],'revision':info['revision'],'args':{'identity':str(identity),'password':'Synthetic-smoke-only-123','path':str(output/'signed.pdf'),'overwrite':True}})
    signature=signed['validation']['signatures'][0]
    assert signature['intact'] and signature['valid'] and not signature['trusted']
    receipt['offline_certificate_signing']=True
    if archival_runtime:
        archived=command({'command':'export','session':info['id'],'args':{'mode':'pdfa_2b','path':str(output/'archival.pdf'),'overwrite':True}})
        assert archived['validation']['compliant'] and archived['validation']['failed_rules']==0
        receipt['configured_free_archival_conversion']=True
    (output/'receipt.json').write_text(json.dumps(receipt,indent=2),encoding='utf-8')
    print(json.dumps(receipt,indent=2))
finally:
    process.terminate()
    process.wait(timeout=20)
