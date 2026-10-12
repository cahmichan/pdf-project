import { chromium } from '@playwright/test';
import { spawn } from 'node:child_process';
import fs from 'node:fs';
import path from 'node:path';
import { createHash } from 'node:crypto';
const root=process.cwd();
const executable=process.argv[2]||path.join(root,'src-tauri','target','release','folio.exe');
const folder=path.join(root,'artifacts','native-smoke');fs.mkdirSync(folder,{recursive:true});
const source=path.join(root,'artifacts','fixtures','unusual-fields.pdf');
const hash=file=>createHash('sha256').update(fs.readFileSync(file)).digest('hex');
const original=hash(source);
const child=spawn(executable,[source],{cwd:path.dirname(executable),windowsHide:true,env:{...process.env,WEBVIEW2_ADDITIONAL_BROWSER_ARGUMENTS:'--remote-debugging-port=9223'}});
let browser;
try {
  for(let attempt=0;attempt<60;attempt++){
    if(child.exitCode!==null)throw new Error(`Native app exited ${child.exitCode}`);
    try{browser=await chromium.connectOverCDP('http://127.0.0.1:9223');break;}catch{await new Promise(resolve=>setTimeout(resolve,500));}
  }
  if(!browser)throw new Error('Native form WebView2 endpoint unavailable.');
  const page=browser.contexts()[0].pages()[0];const errors=[];page.on('pageerror',error=>errors.push(error.message));
  await page.getByRole('button',{name:'Forms',exact:true}).click();
  const expected=new Map([['__proto__','Native proto'],['constructor','Native ctor'],['toString','Native string']]);
  for(const [name,value] of expected)await page.getByLabel(`On-page ${name}`,{exact:true}).fill(value);
  // Print preparation applies drafts, without submitting a physical print job.
  await page.getByRole('button',{name:'Print',exact:true}).click();
  await page.getByLabel('Pages: all or a range such as 1-3,5').fill('all');
  await page.getByRole('button',{name:'Continue',exact:true}).click();
  await page.getByRole('button',{name:'Open print dialog',exact:true}).waitFor();
  await page.waitForFunction(()=>{const button=[...document.querySelectorAll('button')].find(item=>item.textContent==='Open print dialog');return button&&!button.disabled;});
  await page.screenshot({path:path.join(folder,'form-drafts-preview.png')});
  await page.getByRole('button',{name:'Close preview',exact:true}).click();
  for(const [name,value] of expected){
    if(await page.getByLabel(`On-page ${name}`,{exact:true}).inputValue()!==value)throw new Error(`Draft not applied for ${name}`);
  }
  await page.getByRole('button',{name:'Undo',exact:true}).click();
  await page.waitForFunction(()=>[...document.querySelectorAll('.form-control')].length===3&&[...document.querySelectorAll('.form-control')].every(input=>input.value==='Initial'));
  if(errors.length||hash(source)!==original)throw new Error(`Native draft errors: ${JSON.stringify(errors)}`);
  const result={passed:true,executable_sha256:hash(executable),worker_sha256:hash(path.join(path.dirname(executable),'pdf-worker.exe')),unusual_field_names:true,staged_print_preparation_and_undo:true,source_unchanged:true,errors,physical_print_submitted:false};
  fs.writeFileSync(path.join(folder,'form-drafts-receipt.json'),JSON.stringify(result,null,2));console.log(JSON.stringify(result,null,2));
}finally{if(browser)await browser.close();child.kill();}
