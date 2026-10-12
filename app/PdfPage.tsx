import { useEffect, useRef, useState } from 'react';
import { GlobalWorkerOptions, getDocument, TextLayer, type PDFDocumentProxy, type RenderTask } from 'pdfjs-dist';
import workerUrl from 'pdfjs-dist/build/pdf.worker.min.mjs?url';
import 'pdfjs-dist/web/pdf_viewer.css';
import { FormOverlay } from './FormOverlay';
import { documentUrl, type DocumentInfo, type PageInfo } from './api';
GlobalWorkerOptions.workerSrc = workerUrl;

export function PdfPage({document,page,zoom,tool,onSelect,selection,links,onLink,strokes,onStroke,inkWidth,inkColor,fields,fieldValues,onFieldChange,busy}: {
  fields:PageInfo['forms'];fieldValues:Record<string,string|number>;onFieldChange:(id:string,value:string|number)=>void;busy:boolean;
  document:DocumentInfo;page:number;zoom:number;tool:string;
  onSelect:(rect:number[])=>void;selection:number[]|null;
  strokes:number[][][];onStroke:(stroke:number[][])=>void;inkWidth:number;inkColor:string;
  links:PageInfo['links'];onLink:(link:PageInfo['links'][number])=>void;
}) {
  const canvas = useRef<HTMLCanvasElement>(null);
  const textLayer = useRef<HTMLDivElement>(null);
  const wrapper = useRef<HTMLDivElement>(null);
  const start = useRef<[number,number]|null>(null);
  const [dimensions,setDimensions] = useState({width:595,height:842});
  const ink=useRef<number[][]>([]);const [activeInk,setActiveInk]=useState<number[][]>([]);
  const [drag,setDrag] = useState<number[]|null>(null);
  const [error,setError] = useState('');
  const [loading,setLoading] = useState(true);
  const [loaded,setLoaded] = useState<{pdf:PDFDocumentProxy;path:string;revision:number}|null>(null);
  const [rendered,setRendered]=useState<{path:string;revision:number;page:number;zoom:number}|null>(null);
  useEffect(()=>{
    setLoaded(null);
    const task = getDocument({url:documentUrl(document.path,document.revision),enableXfa:false,cMapUrl:'/pdfjs/cmaps/',cMapPacked:true,standardFontDataUrl:'/pdfjs/standard_fonts/',wasmUrl:'/pdfjs/wasm/'});
    let disposed = false;
    task.promise.then(pdf=>{ if (!disposed) {setLoaded({pdf,path:document.path,revision:document.revision}); setLoading(true);} }).catch(e=>{if(!disposed){setError(String(e));setLoading(false);}});
    return ()=>{disposed=true;void task.destroy();};
  },[document.path,document.revision]);
  useEffect(()=>{
    let cancelled = false; let render:RenderTask|undefined; let layer:TextLayer|undefined;
    setLoading(true);setError('');
    async function paint() {
      // Load per revision/page so rendering cannot use a stale document reference.
      try {
        if (!loaded||loaded.path!==document.path||loaded.revision!==document.revision)return;
        const pdfPage = await loaded.pdf.getPage(page);
        if (cancelled || !canvas.current || !textLayer.current) return;
        const viewport = pdfPage.getViewport({scale:zoom});
        const ratio = window.devicePixelRatio || 1;
        setDimensions({width:viewport.width,height:viewport.height});
        canvas.current.width=Math.round(viewport.width*ratio);canvas.current.height=Math.round(viewport.height*ratio);
        canvas.current.style.width=`${viewport.width}px`;canvas.current.style.height=`${viewport.height}px`;
        render=pdfPage.render({canvasContext:canvas.current.getContext('2d')!,viewport,transform:[ratio,0,0,ratio,0,0],canvas:canvas.current});
        await render.promise;
        if (cancelled) return;
        textLayer.current.replaceChildren();
        textLayer.current.style.setProperty('--scale-factor',String(zoom));
        layer=new TextLayer({textContentSource:await pdfPage.getTextContent(),container:textLayer.current,viewport});
        await layer.render();
        if (!cancelled) {setRendered({path:document.path,revision:document.revision,page,zoom});setLoading(false);}
      } catch(e) {if (!cancelled) {setError(String(e));setLoading(false);}}
    }
    void paint();
    return ()=>{cancelled=true;render?.cancel();layer?.cancel();};
  },[loaded,page,zoom,document.path,document.revision]);
  const choose = ['crop','add_text','replace_text','add_image','highlight','underline','strikeout','rectangle','stamp','ink','comment','redact','add_form'].includes(tool);
  function point(event:React.PointerEvent):[number,number] {
    const bounds=wrapper.current!.getBoundingClientRect();
    return [Math.max(0,Math.min(dimensions.width,event.clientX-bounds.left)),Math.max(0,Math.min(dimensions.height,event.clientY-bounds.top))];
  }
  function begin(event:React.PointerEvent) {if(!choose)return;start.current=point(event);if(tool==='ink'){ink.current=[start.current];setActiveInk(ink.current);}event.currentTarget.setPointerCapture(event.pointerId);setDrag(null);}
  function move(event:React.PointerEvent) {if(!start.current)return;const end=point(event);if(tool==='ink'){ink.current=[...ink.current,end];setActiveInk(ink.current);return;}setDrag([Math.min(start.current[0],end[0]),Math.min(start.current[1],end[1]),Math.max(start.current[0],end[0]),Math.max(start.current[1],end[1])]);}
  function finish(event:React.PointerEvent) {
    if (!start.current)return;
    const end=point(event);const origin=start.current;start.current=null;setDrag(null);
    if (tool!=='ink'&&(Math.abs(end[0]-origin[0])<4 || Math.abs(end[1]-origin[1])<4))return;
    const model=document.pages[page-1];
    if(tool==='ink'){const points=[...ink.current,end];ink.current=[];setActiveInk([]);onStroke(points.map(p=>[p[0]*model.width/dimensions.width,p[1]*model.height/dimensions.height]));return;}
    onSelect([Math.min(origin[0],end[0])*model.width/dimensions.width,Math.min(origin[1],end[1])*model.height/dimensions.height,Math.max(origin[0],end[0])*model.width/dimensions.width,Math.max(origin[1],end[1])*model.height/dimensions.height]);
  }
  const ready=rendered?.path===document.path&&rendered.revision===document.revision&&rendered.page===page&&rendered.zoom===zoom;
  const model=document.pages[page-1];
  const shown=drag || (selection && [selection[0]*dimensions.width/model.width,selection[1]*dimensions.height/model.height,selection[2]*dimensions.width/model.width,selection[3]*dimensions.height/model.height]);
  return <div className="paper" data-session={document.id} data-revision={document.revision} data-rendered-revision={ready?document.revision:-1} ref={wrapper} style={{width:dimensions.width,height:dimensions.height}}>
    <canvas ref={canvas}/><div ref={textLayer} className="textLayer" style={{pointerEvents:choose?'none':'auto'}}/>
    {!choose&&links.map((link,index)=><button key={index} className="pdf-link" aria-label={link.uri?`Open link ${link.uri}`:`Go to page ${link.page}`} title={link.uri||`Page ${link.page}`} onClick={()=>onLink(link)} style={{left:link.rect[0]*dimensions.width/model.width,top:link.rect[1]*dimensions.height/model.height,width:(link.rect[2]-link.rect[0])*dimensions.width/model.width,height:(link.rect[3]-link.rect[1])*dimensions.height/model.height}}/>)}
    {choose && ready && <div className="selection-surface" onPointerDown={begin} onPointerMove={move} onPointerUp={finish} onPointerCancel={()=>{start.current=null;setDrag(null);ink.current=[];setActiveInk([]);}}/>}
    {tool==='ink'&&<svg className="ink-preview" width={dimensions.width} height={dimensions.height} aria-label="Ink preview"><g fill="none" stroke={inkColor} strokeWidth={inkWidth*zoom} strokeLinecap="round" strokeLinejoin="round">{strokes.map((stroke,index)=><polyline key={index} points={stroke.map(p=>`${p[0]*dimensions.width/model.width},${p[1]*dimensions.height/model.height}`).join(' ')}/>)}<polyline points={activeInk.map(p=>p.join(',')).join(' ')}/></g></svg>}
    {shown && <div className={`selection-box ${tool==='redact'?'redaction':''}`} style={{left:shown[0],top:shown[1],width:shown[2]-shown[0],height:shown[3]-shown[1]}}/>}
    {tool==='fill_forms'&&ready&&!loading&&<FormOverlay fields={fields} values={fieldValues} onChange={onFieldChange} width={dimensions.width} height={dimensions.height} pageWidth={model.width} pageHeight={model.height} disabled={busy}/>}
    {!error&&(loading||!ready) && <div className="page-loading">Rendering page…</div>}
    {error && <div className="page-error">Unable to render this page: {error}</div>}
  </div>;
}
