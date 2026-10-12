import { chromium } from '@playwright/test';
import { spawn,execFileSync } from 'node:child_process';
import fs from 'node:fs';
import path from 'node:path';
import { createHash } from 'node:crypto';
import { debugPort,stopNative } from './native_test_runtime.mjs';
const root=process.cwd(),port=await debugPort(),executable=process.argv[2]||path.join(root,'src-tauri','target','release','folio.exe');
const folder=path.join(root,'artifacts','native-smoke'),source=path.join(root,'artifacts','fixtures','mixed-styles.pdf'),output=path.join(folder,'styled-text.pdf');
const hash=file=>createHash('sha256').update(fs.readFileSync(file)).digest('hex'),original=hash(source);
const child=spawn(executable,[source],{cwd:path.dirname(executable),windowsHide:true,env:{...process.env,WEBVIEW2_USER_DATA_FOLDER:path.join(folder,`webview-styled-${Date.now()}`),WEBVIEW2_ADDITIONAL_BROWSER_ARGUMENTS:`--remote-debugging-port=${port}`}});
let browser;
try{
  for(let attempt=0;attempt<60;attempt++){
    if(child.exitCode!==null)throw new Error(`Native styled app exited ${child.exitCode}`);
    try{browser=await chromium.connectOverCDP(`http://127.0.0.1:${port}`);break;}catch{await new Promise(resolve=>setTimeout(resolve,500));}
  }
  if(!browser)throw new Error('Native styled WebView unavailable.');
  const page=browser.contexts()[0].pages()[0],errors=[];page.on('pageerror',error=>errors.push(error.message));
  await page.locator('.textLayer').filter({hasText:'$100'}).waitFor();await page.getByRole('button',{name:'Edit',exact:true}).click();
  await page.locator('.textLayer span').filter({hasText:'$100'}).click();const editor=page.getByLabel('Edit text on page');await editor.fill('Total: $125 paid');
  const live=await editor.locator('span').evaluateAll(spans=>spans.map(span=>({text:span.textContent,weight:getComputedStyle(span).fontWeight,color:getComputedStyle(span).color,size:getComputedStyle(span).fontSize,italic:getComputedStyle(span).fontStyle})));
  const amount=live.find(run=>run.text.includes('$125')),paid=live.find(run=>run.text.includes('paid'));
  if(amount?.weight!=='700'||amount.size!=='18px'||amount.color!=='rgb(204, 0, 0)'||paid?.italic!=='italic')throw new Error(`Native live styles mismatch: ${JSON.stringify(live)}`);
  await editor.press('Control+z');if(await editor.textContent()!=='Total: $100 paid')throw new Error('Native draft undo failed.');await editor.press('Control+y');if(await editor.textContent()!=='Total: $125 paid')throw new Error('Native draft redo failed.');
  await page.screenshot({path:path.join(folder,'live-styled-editing.png')});await page.getByRole('button',{name:'Apply text',exact:true}).click();
  await page.locator('.textLayer').filter({hasText:'$125'}).waitFor();await page.screenshot({path:path.join(folder,'styled-text.png')});
  await page.evaluate(async target=>{const invoke=request=>window.__TAURI_INTERNALS__.invoke('pdf_command',{request});return invoke({command:'export',session:document.querySelector('.paper').dataset.session,args:{path:target,overwrite:true}});},output);
  execFileSync(path.join(root,'.venv','Scripts','python.exe'),['-c',"import pymupdf as p,pypdfium2 as v,sys; d=p.open(sys.argv[1]); spans=[s for b in d[0].get_text('dict')['blocks'] if b['type']==0 for l in b['lines'] for s in l['spans']]; a=next(s for s in spans if '$125' in s['text']); assert a['font']=='Helvetica-Bold' and abs(a['size']-18)<.1 and a['color']&0xff0000; b=next(s for s in spans if 'paid' in s['text']); assert b['font']=='Times-Italic' and b['color']&0x00ff00; d.close(); q=v.PdfDocument(sys.argv[1]); assert '$125' in q[0].get_textpage().get_text_range() and q[0].render().to_pil().getbbox(); q.close()",output],{cwd:root,windowsHide:true});
  await page.getByRole('button',{name:'Undo',exact:true}).click();await page.locator('.textLayer').filter({hasText:'$100'}).waitFor();
  if(errors.length||hash(source)!==original)throw new Error(`Native styled editing failed: ${JSON.stringify(errors)}`);
  const receipt={passed:true,executable_sha256:hash(executable),worker_sha256:hash(path.join(path.dirname(executable),'pdf-worker.exe')),live_mixed_styles:true,draft_undo_redo:true,mixed_font_color_size_preserved:true,independent_reopen_render:true,undo:true,source_unchanged:true,errors};
  fs.writeFileSync(path.join(folder,'styled-text-receipt.json'),JSON.stringify(receipt,null,2));console.log(JSON.stringify(receipt,null,2));
}finally{if(browser)await browser.close();stopNative(child);}
