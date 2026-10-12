import { useEffect, useRef, useState } from 'react';
import { command } from './api';
export type ScanPhoto = {name?:string;path:string;hash:string;width:number;height:number;corners:number[][];detected:boolean;preview:string};

export function CameraDialog({onCaptured,onClose,remaining}:{onCaptured:(photo:ScanPhoto)=>void;onClose:()=>void;remaining:number}) {
  const video=useRef<HTMLVideoElement>(null),stream=useRef<MediaStream|null>(null),generation=useRef(0),mounted=useRef(true);
  const [live,setLive]=useState(false),[starting,setStarting]=useState(false),[capturing,setCapturing]=useState(false),[ready,setReady]=useState(false),[error,setError]=useState(''),[device,setDevice]=useState(''),[devices,setDevices]=useState<MediaDeviceInfo[]>([]),[count,setCount]=useState(0);
  function stop(){generation.current++;stream.current?.getTracks().forEach(track=>track.stop());stream.current=null;if(video.current)video.current.srcObject=null;setLive(false);setReady(false);setStarting(false);}
  useEffect(()=>{mounted.current=true;return()=>{mounted.current=false;generation.current++;stream.current?.getTracks().forEach(track=>track.stop());stream.current=null;};},[]);
  async function start(){
    stop();setError('');setStarting(true);const request=++generation.current;
    try{
      if(!navigator.mediaDevices?.getUserMedia)throw new Error('Camera capture is unavailable in this window. Import a photo instead.');
      const next=await navigator.mediaDevices.getUserMedia({audio:false,video:{width:{ideal:1920},height:{ideal:1080},...(device?{deviceId:{exact:device}}:{facingMode:{ideal:'environment'}})}});
      if(!mounted.current||request!==generation.current){next.getTracks().forEach(track=>track.stop());return;}
      stream.current=next;if(video.current){video.current.srcObject=next;await video.current.play();}
      if(!mounted.current||request!==generation.current)return;
      setLive(true);setStarting(false);
      next.getVideoTracks()[0]?.addEventListener('ended',()=>{if(mounted.current&&stream.current===next){stop();setError('The camera disconnected. Start it again or choose another camera.');}},{once:true});
      const listed=await navigator.mediaDevices.enumerateDevices();
      if(mounted.current&&request===generation.current){setDevices(listed.filter(item=>item.kind==='videoinput'));setDevice(next.getVideoTracks()[0]?.getSettings().deviceId||'');}
    }catch(e){
      if(!mounted.current||request!==generation.current)return;
      stop();const name=(e as Error).name;
      setError(name==='NotAllowedError'?'Camera permission was denied. Allow camera access in Windows/WebView2, or import a photo.':name==='NotFoundError'?'No camera was found. Connect a camera or import a photo.':name==='NotReadableError'?'The camera could not be opened. Close other apps using it and try again.':String(e).replace(/^Error: /,''));
    }
  }
  async function capture(){
    const source=video.current;if(!source||!ready||!source.videoWidth||remaining<1)return;
    setCapturing(true);setError('');
    try{
      const ratio=Math.min(1,3000/Math.max(source.videoWidth,source.videoHeight));
      const canvas=document.createElement('canvas');canvas.width=Math.round(source.videoWidth*ratio);canvas.height=Math.round(source.videoHeight*ratio);
      const context=canvas.getContext('2d');if(!context)throw new Error('Could not prepare the camera frame.');context.drawImage(source,0,0,canvas.width,canvas.height);
      const photo=await command<ScanPhoto>('scan_capture',null,{image:canvas.toDataURL('image/jpeg',.94)});
      if(mounted.current){onCaptured(photo);setCount(value=>value+1);}
    }catch(e){if(mounted.current)setError(String(e).replace(/^Error: /,''));}finally{if(mounted.current)setCapturing(false);}
  }
  return <div className="modal-backdrop camera-backdrop"><section className="camera-dialog" role="dialog" aria-modal="true" aria-label="Capture document with camera">
    <header><h2>Capture document with camera</h2><button aria-label="Close camera" onClick={()=>{stop();onClose();}}>×</button></header>
    <p>Place the document in view with clear edges. Capture a photo, then review its corners and enhancement in the scanner.</p>
    <video ref={video} autoPlay muted playsInline aria-label="Live camera preview" onLoadedData={()=>setReady(true)} onEmptied={()=>setReady(false)}/>
    {devices.length>0&&<label>Camera<select aria-label="Camera device" disabled={starting||capturing||live} value={device} onChange={event=>setDevice(event.target.value)}>{devices.map(item=><option key={item.deviceId} value={item.deviceId}>{item.label||'Camera'}</option>)}</select></label>}
    {error&&<p role="alert" className="notice warning">{error}</p>}
    <p role="status">{starting?'Waiting for camera permission…':live?'Camera is on. Audio is off.':'Camera is off.'} {count>0?`${count} photo${count===1?'':'s'} added.`:''}</p>
    <footer><button disabled={capturing||(!live&&!starting)} onClick={stop}>Stop camera</button><button disabled={starting||capturing||live} onClick={()=>void start()}>Start camera</button><button className="primary" disabled={!live||!ready||capturing||remaining<1} onClick={()=>void capture()}>{capturing?'Capturing…':'Capture photo'}</button><button disabled={capturing} onClick={()=>{stop();onClose();}}>Done</button></footer>
  </section></div>;
}
