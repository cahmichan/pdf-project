import { useEffect, useLayoutEffect, useRef, useState } from 'react';
export type TextDraft={documentId:string;page:number;kind:'edit'|'add';expected:string;sourceRect:number[];rect:number[];point:number[];text:string;size:number;color:string;font:string;sourceFont:string;sourceSize:number;sourceColor:string;flags:number;rotation:number;caret?:number;selectedText?:string};
const fonts=[['original','Original font'],['helv','Helvetica'],['hebo','Helvetica bold'],['heit','Helvetica italic'],['tiro','Times'],['tibo','Times bold'],['tiit','Times italic'],['cour','Courier']];
export function InlineTextEditor({draft,zoom,pageWidth,pageHeight,busy,onChange,onApply,onCancel}:{draft:TextDraft;zoom:number;pageWidth:number;pageHeight:number;busy:boolean;onChange:(draft:TextDraft)=>void;onApply:()=>void;onCancel:()=>void}){
  const input=useRef<HTMLTextAreaElement>(null);const [height,setHeight]=useState(28);
  const rawWidth=draft.kind==='edit'?draft.sourceRect[2]-draft.sourceRect[0]:180;
  const [width,setWidth]=useState(Math.max(100,rawWidth)*zoom);
  const centerX=(draft.rect[0]+draft.rect[2])/2*zoom,centerY=(draft.rect[1]+draft.rect[3])/2*zoom;
  const rotation=draft.kind==='edit'?draft.rotation:0;
  const x=draft.kind==='edit'&&rotation?centerX-rawWidth*zoom/2:draft.rect[0]*zoom,y=draft.kind==='edit'&&rotation?centerY-(draft.sourceRect[3]-draft.sourceRect[1])*zoom/2:draft.rect[1]*zoom;
  const family=draft.font.startsWith('ti')?'Times New Roman':draft.font.startsWith('co')?'Courier New':'Arial';
  const bold=['hebo','hebi','tibo','tibi','cobo','cobi'].includes(draft.font)||(draft.font==='original'&&!!(draft.flags&16));
  const italic=['heit','hebi','tiit','tibi','coit','cobi'].includes(draft.font)||(draft.font==='original'&&!!(draft.flags&2));
  useLayoutEffect(()=>{
    if(!input.current)return;
    const canvas=document.createElement('canvas'),context=canvas.getContext('2d');
    if(context){context.font=`${italic?'italic ':''}${bold?'bold ':''}${draft.size*zoom}px ${family}`;const measured=Math.max(...draft.text.split('\n').map(line=>context.measureText(line||' ').width))+8;setWidth(Math.max(40,Math.min((rotation?Math.max(pageWidth,pageHeight):pageWidth-draft.rect[0])*zoom-4,Math.max(rawWidth*zoom,measured))));}
    input.current.style.height='auto';setHeight(Math.max(draft.size*zoom*1.35,input.current.scrollHeight));
  },[draft.text,draft.size,draft.font,width,zoom,pageWidth,pageHeight]);
  useEffect(()=>{const element=input.current;if(!element)return;element.focus();const selected=draft.selectedText?draft.text.indexOf(draft.selectedText):-1;const caret=draft.caret??draft.text.length;element.setSelectionRange(selected>=0?selected:caret,selected>=0?selected+draft.selectedText!.length:caret);},[draft.expected,draft.kind,draft.sourceRect.join(','),draft.point.join(',')]);
  return <>
    {draft.kind==='edit'&&<div className="inline-text-mask" style={{left:draft.rect[0]*zoom,top:draft.rect[1]*zoom,width:(draft.rect[2]-draft.rect[0])*zoom,height:(draft.rect[3]-draft.rect[1])*zoom}}/>}
    <textarea ref={input} className="inline-text-editor" aria-label={draft.kind==='edit'?'Edit text on page':'New text on page'} spellCheck={false} disabled={busy} value={draft.text} style={{left:x,top:y,width,height,fontFamily:family,fontSize:draft.size*zoom,color:draft.color,fontWeight:bold?'bold':'normal',fontStyle:italic?'italic':'normal',transform:rotation?`rotate(${rotation}deg)`:undefined,transformOrigin:rotation?`${rawWidth*zoom/2}px ${(draft.sourceRect[3]-draft.sourceRect[1])*zoom/2}px`:undefined}} onChange={event=>onChange({...draft,text:event.target.value})} onKeyDown={event=>{if(event.key==='Escape'){event.preventDefault();onCancel();}if(event.key==='Enter'&&(event.ctrlKey||event.metaKey)){event.preventDefault();onApply();}}}/>
    <div className="inline-text-toolbar" style={{left:Math.min(draft.rect[0]*zoom,Math.max(0,pageWidth*zoom-420)),top:Math.max(0,draft.rect[1]*zoom-52)}}>
      <label>Font<select aria-label="Text font" disabled={busy} value={draft.font} onChange={event=>onChange({...draft,font:event.target.value})}>{fonts.filter(([value])=>value!=='original'||draft.kind==='edit').map(([value,label])=><option key={value} value={value}>{value==='original'?`${label} (${draft.sourceFont})`:label}</option>)}</select></label>
      <label>Size<input aria-label="Text size" type="number" min="1" max="300" disabled={busy} value={draft.size} onChange={event=>onChange({...draft,size:Number(event.target.value)})}/></label><input aria-label="Text color" type="color" disabled={busy} value={draft.color} onChange={event=>onChange({...draft,color:event.target.value})}/><button disabled={busy||(draft.kind==='add'&&!draft.text.trim())} onClick={onApply}>Apply text</button><button disabled={busy} onClick={onCancel}>Cancel text</button>
    </div>
  </>;
}
