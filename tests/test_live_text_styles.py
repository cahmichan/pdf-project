import json
from pathlib import Path
import random
import shutil
import subprocess
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'worker'))
import pymupdf as pdf
from direct_text import paragraphs
from styled_text import mapped_styles,source_styles


def test_browser_style_mapping_matches_pdf_rules_for_unicode_ties_and_repeated_text():
    rng=random.Random(1800);cases=[];expected=[]
    for index in range(160):
        before=''.join(rng.choice('aa bbΣ🙂中\n') for _ in range(rng.randint(1,45)))
        after=before
        for _ in range(3):
            a=rng.randint(0,len(after));b=rng.randint(a,len(after));after=after[:a]+''.join(rng.choice('ab 🙂中\n') for _ in range(rng.randint(0,6)))+after[b:]
        styles=[{'font':'Run'+str(i%3),'size':12+i%3,'color':('#000000','#cc0000','#004c00')[i%3],'flags':i%3,'offset':i%2} for i in range(len(before))]
        ratio=2 if index%2 else 1;color='#ff0000' if index%4 else '#000000';mode=('auto','uniform','original')[index%3]
        cases.append({'before':before,'source':[{**style,'text':char} for char,style in zip(before,styles)],'after':after,'size':12*ratio,'sourceSize':12,'color':color,'sourceColor':'#000000','colorMode':mode})
        override=mode=='uniform' or (mode=='auto' and color!='#000000')
        expected.append([{**style,'size':style['size']*ratio,'offset':style['offset']*ratio,'color':color if override else style['color'],'text':char} for char,style in zip(after,mapped_styles(before,styles,after))])
    code="""import fs from 'node:fs';import ts from 'typescript';
const compiled=ts.transpile(fs.readFileSync('app/text-styles.ts','utf8'),{module:ts.ModuleKind.ESNext,target:ts.ScriptTarget.ES2022});
const {liveRuns}=await import('data:text/javascript;base64,'+Buffer.from(compiled).toString('base64'));
const cases=JSON.parse(fs.readFileSync(0,'utf8'));console.log(JSON.stringify(cases.map(c=>liveRuns(c.before,c.source,c.after,c.size,c.sourceSize,c.color,c.sourceColor,c.colorMode).flatMap(r=>Array.from(r.text,char=>({...r,text:char}))))));"""
    run=subprocess.run([shutil.which('node'),'--input-type=module','-e',code],input=json.dumps(cases,ensure_ascii=False),encoding='utf-8',capture_output=True,cwd=Path(__file__).resolve().parents[1],check=True)
    assert json.loads(run.stdout)==expected


def test_inspected_runs_match_engine_styles_including_line_breaks():
    with pdf.open() as doc:
        page=doc.new_page();page.insert_text((40,80),'Plain ',fontsize=14)
        page.insert_text((78,80),'bold',fontname='hebo',fontsize=18,color=(.8,0,0))
        page.insert_text((40,100),'Next line',fontname='tiit',fontsize=14)
        for paragraph in paragraphs(page):
            before,styles=source_styles(page,paragraph['id'])
            actual=[{key:value for key,value in run.items() if key!='text'} for run in paragraph['runs'] for _ in run['text']]
            assert ''.join(run['text'] for run in paragraph['runs'])==before==paragraph['text']
            assert actual==styles
