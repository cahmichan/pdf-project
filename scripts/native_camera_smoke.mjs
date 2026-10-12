import { debugPort, stopNative } from './native_test_runtime.mjs';
import { chromium } from '@playwright/test';
import { spawn } from 'node:child_process';
import fs from 'node:fs';
import path from 'node:path';
import { createHash } from 'node:crypto';
const port=await debugPort();
const root=process.cwd(),executable=process.argv[2]||path.join(root,'src-tauri','target','release','folio.exe');
const folder=path.join(root,'artifacts','native-smoke'),video=path.join(root,'artifacts','fixtures','camera.y4m');
const hash=file=>createHash('sha256').update(fs.readFileSync(file)).digest('hex');
if(!fs.existsSync(video))throw new Error('Prepare the synthetic camera video with the browser camera test first.');
const fixtureHash=hash(video);
const child=spawn(executable,[],{cwd:path.dirname(executable),windowsHide:true,env:{...process.env,WEBVIEW2_USER_DATA_FOLDER:path.join(folder,`webview-camera-${Date.now()}`),WEBVIEW2_ADDITIONAL_BROWSER_ARGUMENTS:`--remote-debugging-port=${port} --use-fake-device-for-media-stream --use-fake-ui-for-media-stream --use-file-for-fake-video-capture="${video.replaceAll('\\','/')}"`}});
let browser;
try{
  for(let attempt=0;attempt<60;attempt++){
    if(child.exitCode!==null)throw new Error(`Native camera app exited ${child.exitCode}`);
    try{browser=await chromium.connectOverCDP(`http://127.0.0.1:${port}`);break;}catch{await new Promise(resolve=>setTimeout(resolve,500));}
  }
  if(!browser)throw new Error('Native camera WebView2 endpoint unavailable.');
  const page=browser.contexts()[0].pages()[0],errors=[];page.on('pageerror',error=>errors.push(error.message));
  await page.getByRole('button',{name:'Scan photos',exact:true}).waitFor();
  const cdp=await browser.newBrowserCDPSession();
  await cdp.send('Browser.grantPermissions',{origin:new URL(page.url()).origin,permissions:['videoCapture']});
  const capability=await page.evaluate(async()=>({secure:window.isSecureContext,devices:(await navigator.mediaDevices.enumerateDevices()).filter(device=>device.kind==='videoinput').map(device=>device.label)}));
  // Do not request a video stream unless the read-only inventory proves the fake fixture is active.
  if(!capability.secure||!capability.devices.length||capability.devices.some(label=>!label.replaceAll('\\','/').endsWith('/camera.y4m')))throw new Error(`Synthetic camera was not confirmed; no stream requested: ${JSON.stringify(capability)}`);
  await page.getByRole('button',{name:'Scan photos',exact:true}).click();
  await page.getByRole('button',{name:'Use camera',exact:true}).click();
  await page.getByRole('button',{name:'Start camera',exact:true}).click();
  await page.getByRole('button',{name:'Capture photo',exact:true}).waitFor();
  await page.waitForFunction(()=>{const button=[...document.querySelectorAll('button')].find(item=>item.textContent==='Capture photo');return button&&!button.disabled;});
  await page.evaluate(()=>{window.cameraTestTracks=document.querySelector('video').srcObject.getTracks();});
  await page.getByRole('button',{name:'Capture photo',exact:true}).click();
  await page.getByRole('status').filter({hasText:'1 photo added.'}).waitFor();
  await page.getByRole('button',{name:'Capture photo',exact:true}).click();
  await page.getByRole('status').filter({hasText:'2 photos added.'}).waitFor();
  await page.screenshot({path:path.join(folder,'camera-capture.png')});
  await page.getByRole('button',{name:'Done',exact:true}).click();
  if(!await page.evaluate(()=>window.cameraTestTracks.every(track=>track.readyState==='ended')))throw new Error('Native camera tracks remained live after closing.');
  await page.getByRole('button',{name:'Create scanned PDF',exact:true}).click();
  await page.getByRole('dialog',{name:'Scan photos to PDF'}).waitFor({state:'hidden'});
  await page.locator('.page-loading').waitFor({state:'hidden'});
  const reopened=await page.evaluate(async target=>{
    const invoke=request=>window.__TAURI_INTERNALS__.invoke('pdf_command',{request}),session=document.querySelector('.paper').dataset.session;
    const saved=await invoke({command:'export',session,args:{path:target,overwrite:true}});
    return invoke({command:'open',args:{path:saved.path}});
  },path.join(folder,'camera-scanned.pdf'));
  if(reopened.page_count!==2||errors.length||hash(video)!==fixtureHash)throw new Error(`Native synthetic capture failed: ${JSON.stringify(errors)}`);
  const result={passed:true,executable_sha256:hash(executable),worker_sha256:hash(path.join(path.dirname(executable),'pdf-worker.exe')),synthetic_video_sha256:fixtureHash,native_camera_ui:true,two_captures_create_export_reopen:true,tracks_stopped:true,real_camera_used:false,errors,manual_checks_remaining:['real camera permission and capture','native file dialogs']};
  fs.writeFileSync(path.join(folder,'camera-receipt.json'),JSON.stringify(result,null,2));console.log(JSON.stringify(result,null,2));
}catch(error){if(browser){const page=browser.contexts()[0].pages()[0];console.error(await page.locator('body').innerText());await page.screenshot({path:path.join(folder,'camera-failure.png')});}throw error;}finally{if(browser)await browser.close();stopNative(child);}
