"""Synthetic local throughput measurements, not general performance guarantees."""
import json
from pathlib import Path
import sys
import time
import pymupdf as pdf
root=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(root/'worker'))
from engine import Engine, fingerprint
folder=root/'artifacts'/'benchmark';folder.mkdir(parents=True,exist_ok=True)
source=folder/'large-500.pdf'
if not source.exists():
    doc=pdf.open()
    for n in range(500):
        page=doc.new_page();page.insert_text((40,60),f'Large synthetic page {n+1}',fontsize=18)
        for line in range(30):page.insert_text((40,95+line*19),f'Reference {n+1:03}-{line:02}: searchable synthetic content.',fontsize=11)
    doc.save(source,deflate=True);doc.close()
original=fingerprint(source);engine=Engine(folder/'data')
start=time.perf_counter();session=engine.dispatch({'command':'open','args':{'path':str(source)}});opening=time.perf_counter()-start
start=time.perf_counter();engine.dispatch({'command':'thumbnail','session':session['id'],'args':{'page':1}});thumbnail=time.perf_counter()-start
start=time.perf_counter();hits=engine.dispatch({'command':'search','session':session['id'],'args':{'text':'Reference 500-29'}});search=time.perf_counter()-start
assert hits[0]['page']==500 and fingerprint(source)==original
receipt={'fixture':str(source),'pages':500,'bytes':source.stat().st_size,'engine_open_seconds':round(opening,3),'first_thumbnail_seconds':round(thumbnail,3),'full_search_seconds':round(search,3),'source_unchanged':True,'note':'One synthetic digital-text fixture on this computer. Does not measure native cold startup, complex scans, or peak memory.'}
(folder/'receipt.json').write_text(json.dumps(receipt,indent=2),encoding='utf-8');print(json.dumps(receipt,indent=2))
