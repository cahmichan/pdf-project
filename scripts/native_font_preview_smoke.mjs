import { chromium } from '@playwright/test';
import { spawn,execFileSync } from 'node:child_process';
import fs from 'node:fs';
import path from 'node:path';
import { createHash } from 'node:crypto';
import { debugPort,stopNative } from './native_test_runtime.mjs';
const root=process.cwd(),executable=process.argv[2]||path.join(root,'src-tauri','target','release','folio.exe'),folder=path.join(root,'artifacts','native-smoke');
const hash=file=>createHash('sha256').update(fs.readFileSync(file)).digest('hex');
for(const [fixture,changed] of [['font-preview.pdf','Hello Σ native 中文'],['cff-preview.pdf','CFF native café Σ']]){
  const port=await debugPort(),source=path.join(root,'artifacts','fixtures',fixture),original=hash(source),output=path.join(folder,'native-'+fixture);
  const child=spawn(executable,[source],{cwd:path.dirname(executable),windowsHide:true,env:{...process.env,WEBVIEW2_USER_DATA_FOLDER:path.join(folder,`webview-font-${fixture}-${Date.now()}`),WEBVIEW2_ADDITIONAL_BROWSER_ARGUMENTS:`--remote-debugging-port=${port}`}});let browser;
  try{
    for(let attempt=0;attempt<60;attempt++){if(child.exitCode!==null)throw new Error('Native font app exited.');try{browser=await chromium.connectOverCDP(`http://127.0.0.1:${port}`);break;}catch{await new Promise(resolve=>setTimeout(resolve,500));}}
    if(!browser)throw new Error('Native font WebView unavailable.');
    const page=browser.contexts()[0].pages()[0],errors=[];page.on('pageerror',error=>errors.push(error.message));
    await page.locator('.textLayer').filter({hasText:'café'}).waitFor();await page.getByRole('button',{name:'Edit',exact:true}).click();await page.locator('.textLayer span').filter({hasText:'café'}).click();await page.getByText('Original embedded fonts loaded for preview.',{exact:true}).waitFor();
    const editor=page.getByLabel('Edit text on page');await editor.fill(changed);const family=await editor.locator('span').first().evaluate(element=>getComputedStyle(element).fontFamily);if(!family.includes('FolioPreview_'))throw new Error('Native original font not selected.');
    await page.screenshot({path:path.join(folder,'native-'+fixture+'.png')});await editor.press('Control+Enter');await editor.waitFor({state:'hidden'});await page.locator('.textLayer').filter({hasText:'native'}).waitFor();
    if(await page.evaluate(()=>[...document.fonts].some(face=>face.family.startsWith('FolioPreview_'))))throw new Error('Native preview font remained registered.');
    await page.evaluate(async target=>window.__TAURI_INTERNALS__.invoke('pdf_command',{request:{command:'export',session:document.querySelector('.paper').dataset.session,args:{path:target,overwrite:true}}}),output);
    execFileSync(path.join(root,'.venv','Scripts','python.exe'),['-c',"import pypdfium2 as p,sys; d=p.PdfDocument(sys.argv[1]); t=d[0].get_textpage().get_text_range(); assert 'native' in t and 'Σ' in t and 'Keep neighbor' in t; assert ('中文' in t) if 'font-preview' in sys.argv[1] else ('café' in t); d[0].render(); d.close()",output],{cwd:root,windowsHide:true});
    if(errors.length||hash(source)!==original)throw new Error(`Native font output failed: ${JSON.stringify(errors)}`);
  }finally{if(browser)await browser.close();stopNative(child);}
}
const receipt={passed:true,executable_sha256:hash(executable),worker_sha256:hash(path.join(path.dirname(executable),'pdf-worker.exe')),original_ttf_cff_loaded:true,unicode_edit_save_reopen:true,preview_faces_released:true,source_unchanged:true,errors:[]};
fs.writeFileSync(path.join(folder,'font-preview-receipt.json'),JSON.stringify(receipt,null,2));console.log(JSON.stringify(receipt,null,2));
