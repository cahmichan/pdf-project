import { chromium } from '@playwright/test';
import { spawn,execFileSync } from 'node:child_process';
import fs from 'node:fs';
import path from 'node:path';
import { createHash } from 'node:crypto';
import { debugPort,stopNative } from './native_test_runtime.mjs';
const root=process.cwd(),port=await debugPort(),executable=process.argv[2]||path.join(root,'src-tauri','target','release','folio.exe');
const folder=path.join(root,'artifacts','native-smoke'),hash=file=>createHash('sha256').update(fs.readFileSync(file)).digest('hex');
const source=path.join(root,'artifacts','fixtures','scan-chinese.pdf'),original=hash(source),output=path.join(folder,'multilingual-ocr.pdf');
const child=spawn(executable,[source],{cwd:path.dirname(executable),windowsHide:true,env:{...process.env,WEBVIEW2_USER_DATA_FOLDER:path.join(folder,`webview-languages-${Date.now()}`),WEBVIEW2_ADDITIONAL_BROWSER_ARGUMENTS:`--remote-debugging-port=${port}`}});
let browser;
try{
  for(let attempt=0;attempt<60;attempt++){
    if(child.exitCode!==null)throw new Error(`Native app exited ${child.exitCode}`);
    try{browser=await chromium.connectOverCDP(`http://127.0.0.1:${port}`);break;}catch{await new Promise(resolve=>setTimeout(resolve,500));}
  }
  if(!browser)throw new Error('Native OCR WebView unavailable.');
  const page=browser.contexts()[0].pages()[0],errors=[];page.on('pageerror',error=>errors.push(error.message));
  await page.locator('.paper').waitFor();await page.locator('.page-loading').waitFor({state:'hidden'});
  await page.getByRole('button',{name:'Convert',exact:true}).click();await page.getByLabel('Tool',{exact:true}).selectOption('ocr');
  await page.getByLabel('OCR language').selectOption('eng+msa+chi_sim');await page.getByRole('button',{name:'Apply to working copy'}).click();
  await page.locator('.textLayer').filter({hasText:'86420'}).waitFor();await page.locator('.page-loading').waitFor({state:'hidden'});
  await page.waitForFunction(()=>{const paper=document.querySelector('.paper');return paper?.dataset.renderedRevision===paper?.dataset.revision;});
  await page.screenshot({path:path.join(folder,'multilingual-ocr.png')});
  await page.evaluate(async target=>window.__TAURI_INTERNALS__.invoke('pdf_command',{request:{command:'export',session:document.querySelector('.paper').dataset.session,args:{path:target,overwrite:true}}}),output);
  execFileSync(path.join(root,'.venv','Scripts','python.exe'),['-c',"import pypdfium2 as p,sys; a=p.PdfDocument(sys.argv[1]); b=p.PdfDocument(sys.argv[2]); t=b[0].get_textpage().get_text_range().replace(' ',''); assert '86420' in t and '文件' in t and '测试' in t; assert a[0].render().to_pil().tobytes()==b[0].render().to_pil().tobytes(); a.close(); b.close()",source,output],{cwd:root,windowsHide:true});
  if(errors.length||hash(source)!==original)throw new Error(`Native multilingual OCR failed: ${JSON.stringify(errors)}`);
  const receipt={passed:true,executable_sha256:hash(executable),worker_sha256:hash(path.join(path.dirname(executable),'pdf-worker.exe')),combined_languages:true,independent_reopen_pixels_preserved:true,source_unchanged:true,errors};
  fs.writeFileSync(path.join(folder,'multilingual-ocr-receipt.json'),JSON.stringify(receipt,null,2));console.log(JSON.stringify(receipt,null,2));
}finally{if(browser)await browser.close();stopNative(child);}
