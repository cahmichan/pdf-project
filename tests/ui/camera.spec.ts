import { test, expect, chromium } from '@playwright/test';
import path from 'node:path';
import { execFileSync } from 'node:child_process';
const root=process.cwd(),python=path.join(root,'.venv','Scripts','python.exe');

test('synthetic camera captures scans, stops tracks and handles permission cancellation',async()=>{
  const photo=path.join(root,'artifacts','fixtures','camera-photo.png'),video=path.join(root,'artifacts','fixtures','camera.y4m');
  execFileSync(python,['-c',"import runpy,sys,cv2; from pathlib import Path; runpy.run_path('tests/test_scanning.py')['photo'](Path(sys.argv[1])); image=cv2.imread(sys.argv[1]); frame=cv2.cvtColor(image,cv2.COLOR_BGR2YUV_I420).tobytes(); Path(sys.argv[2]).write_bytes(b'YUV4MPEG2 W800 H950 F30:1 Ip A1:1 C420jpeg\\n'+b'FRAME\\n'+frame)",photo,video],{cwd:root});
  const browser=await chromium.launch({channel:'msedge',headless:true,args:['--use-fake-device-for-media-stream','--use-fake-ui-for-media-stream',`--use-file-for-fake-video-capture=${video}`]});
  try{
    const context=await browser.newContext({viewport:{width:1440,height:1000}}),page=await context.newPage(),errors:string[]=[];
    page.on('pageerror',error=>errors.push(error.message));
    await page.goto('http://127.0.0.1:1420');
    await page.getByRole('button',{name:'Scan photos',exact:true}).click();
    await page.getByRole('button',{name:'Use camera',exact:true}).click();
    await expect(page.getByRole('status')).toContainText('Camera is off.');
    await expect(page.getByRole('button',{name:'Capture photo',exact:true})).toBeDisabled();
    await page.getByRole('button',{name:'Start camera',exact:true}).click();
    await expect(page.getByRole('button',{name:'Capture photo',exact:true})).toBeEnabled();
    await page.evaluate(()=>{(window as any).cameraTracks=(document.querySelector('video')!.srcObject as MediaStream).getTracks();});
    await page.getByRole('button',{name:'Capture photo',exact:true}).click();
    await expect(page.getByRole('status')).toContainText('1 photo added.');
    await page.getByRole('button',{name:'Capture photo',exact:true}).click();
    await expect(page.getByRole('status')).toContainText('2 photos added.');
    await page.screenshot({path:'artifacts/ui/camera-capture.png',fullPage:true});
    await page.getByRole('button',{name:'Done',exact:true}).click();
    expect(await page.evaluate(()=>(window as any).cameraTracks.every((track:MediaStreamTrack)=>track.readyState==='ended'))).toBeTruthy();
    await expect(page.getByLabel('Scan page').locator('option')).toHaveCount(2);
    await page.getByRole('button',{name:'Preview scan',exact:true}).click();
    await expect(page.getByAltText('Corrected scan preview')).toBeVisible();
    // Hold a fake-camera permission response, then close before it resolves.
    await page.evaluate(()=>{
      const original=navigator.mediaDevices.getUserMedia.bind(navigator.mediaDevices);(window as any).cameraOriginal=original;
      navigator.mediaDevices.getUserMedia=async constraints=>{const stream=await original(constraints);(window as any).pendingCameraTracks=stream.getTracks();return new Promise(resolve=>{(window as any).resumeCamera=()=>resolve(stream);});};
    });
    await page.getByRole('button',{name:'Use camera',exact:true}).click();
    await page.getByRole('button',{name:'Start camera',exact:true}).click();
    await page.waitForFunction(()=>Boolean((window as any).resumeCamera));
    await page.getByRole('button',{name:'Close camera',exact:true}).click();
    await page.evaluate(()=>(window as any).resumeCamera());
    await page.waitForFunction(()=>(window as any).pendingCameraTracks.every((track:MediaStreamTrack)=>track.readyState==='ended'));
    await page.evaluate(()=>{navigator.mediaDevices.getUserMedia=async()=>{throw new DOMException('Synthetic denied','NotAllowedError');};});
    await page.getByRole('button',{name:'Use camera',exact:true}).click();
    await page.getByRole('button',{name:'Start camera',exact:true}).click();
    await expect(page.getByRole('alert')).toContainText('Camera permission was denied');
    await page.getByRole('button',{name:'Close camera',exact:true}).click();
    await page.getByRole('button',{name:'Create scanned PDF',exact:true}).click();
    await expect(page.getByRole('dialog',{name:'Scan photos to PDF'})).toHaveCount(0);
    await expect(page.getByRole('button',{name:/Page 2 thumbnail/})).toBeVisible();
    await expect(page.locator('.page-loading')).toBeHidden();
    expect(errors).toEqual([]);
  }finally{await browser.close();}
});
