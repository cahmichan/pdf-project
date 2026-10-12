import { useEffect, useLayoutEffect, useMemo, useRef, useState } from 'react';
import type { TextRun } from './api';
import { browserStyle, liveRuns } from './text-styles';
export type TextDraft={documentId:string;page:number;kind:'edit'|'add';expected:string;sourceRect:number[];rect:number[];point:number[];text:string;size:number;color:string;font:string;sourceFont:string;mixedStyles?:boolean;sourceRuns?:TextRun[];sourceSize:number;sourceColor:string;flags:number;rotation:number;caret?:number;selectedText?:string};
const fonts=[['original','Original font'],['helv','Helvetica'],['hebo','Helvetica bold'],['heit','Helvetica italic'],['tiro','Times'],['tibo','Times bold'],['tiit','Times italic'],['cour','Courier']];
type Selection={start:number;end:number};
function selectionIn(element:HTMLElement):Selection|null{
  const selection=window.getSelection();if(!selection?.rangeCount)return null;const range=selection.getRangeAt(0);
  if(!element.contains(range.startContainer)||!element.contains(range.endContainer))return null;
  const before=range.cloneRange();before.selectNodeContents(element);before.setEnd(range.startContainer,range.startOffset);const start=before.toString().length;
  return {start,end:start+range.toString().length};
}
function restoreSelection(element:HTMLElement,value:Selection){
  const range=document.createRange(),walker=document.createTreeWalker(element,NodeFilter.SHOW_TEXT);let node=walker.nextNode(),offset=0,startSet=false,endSet=false;
  while(node){const length=node.textContent?.length||0;if(!startSet&&value.start<=offset+length){range.setStart(node,Math.max(0,value.start-offset));startSet=true;}if(!endSet&&value.end<=offset+length){range.setEnd(node,Math.max(0,value.end-offset));endSet=true;break;}offset+=length;node=walker.nextNode();}
  if(!startSet){range.selectNodeContents(element);range.collapse(false);}else if(!endSet)range.collapse(false);
  const selection=window.getSelection();selection?.removeAllRanges();selection?.addRange(range);
}
export function InlineTextEditor({draft,zoom,pageWidth,pageHeight,busy,onChange,onApply,onCancel}:{draft:TextDraft;zoom:number;pageWidth:number;pageHeight:number;busy:boolean;onChange:(draft:TextDraft)=>void;onApply:()=>void;onCancel:()=>void}){
  const input=useRef<HTMLDivElement>(null),composition=useRef(false),savedSelection=useRef<Selection|null>(null),undo=useRef<TextDraft[]>([]),redo=useRef<TextDraft[]>([]);
  const [height,setHeight]=useState(28),[width,setWidth]=useState(100*zoom);
  const rawWidth=draft.kind==='edit'?draft.sourceRect[2]-draft.sourceRect[0]:180;
  const centerX=(draft.rect[0]+draft.rect[2])/2*zoom,centerY=(draft.rect[1]+draft.rect[3])/2*zoom,rotation=draft.kind==='edit'?draft.rotation:0;
  const x=draft.kind==='edit'&&rotation?centerX-rawWidth*zoom/2:draft.rect[0]*zoom,y=draft.kind==='edit'&&rotation?centerY-(draft.sourceRect[3]-draft.sourceRect[1])*zoom/2:draft.rect[1]*zoom;
  const runs=useMemo(()=>{
    if(draft.font==='original'&&draft.mixedStyles&&draft.sourceRuns&&Array.from(draft.expected).length<=5000&&Array.from(draft.text).length<=5000){const mapped=liveRuns(draft.expected,draft.sourceRuns,draft.text,draft.size,draft.sourceSize,draft.color,draft.sourceColor);if(mapped.length)return mapped;}
    return [{text:draft.text,font:draft.font==='original'?draft.sourceFont:draft.font,size:draft.size,color:draft.color,flags:draft.font==='original'?draft.flags:0,offset:0}];
  },[draft.text,draft.font,draft.size,draft.color,draft.expected,draft.sourceRuns]);
  function change(next:TextDraft){undo.current.push(draft);if(undo.current.length>100)undo.current.shift();redo.current=[];onChange(next);}
  function read(){const element=input.current;if(!element||busy)return;savedSelection.current=selectionIn(element);const text=element.textContent||'';if(text!==draft.text)change({...draft,text});}
  function insert(text:string){const element=input.current;if(!element||busy)return;element.focus();if(savedSelection.current)restoreSelection(element,savedSelection.current);const selection=window.getSelection();if(!selection?.rangeCount)return;const range=selection.getRangeAt(0);if(!element.contains(range.commonAncestorContainer))return;range.deleteContents();const node=document.createTextNode(text.replace(/\r\n?/g,'\n').replace(/\t/g,'    '));range.insertNode(node);range.setStartAfter(node);range.collapse(true);selection.removeAllRanges();selection.addRange(range);read();}
  useLayoutEffect(()=>{
    const element=input.current;if(!element||composition.current)return;
    const active=document.activeElement===element,selection=savedSelection.current||selectionIn(element);
    element.replaceChildren(...runs.map(run=>{const span=document.createElement('span');span.textContent=run.text;const style=browserStyle(run.font,run.flags);Object.assign(span.style,{...style,fontSize:`${run.size*zoom}px`,color:run.color,position:'relative',top:`${run.offset*zoom}px`});return span;}));
    if(!draft.text||draft.text.endsWith('\n'))element.appendChild(document.createElement('br'));
    if(active&&selection)restoreSelection(element,selection);
    const context=document.createElement('canvas').getContext('2d');let line=0,longest=0;
    if(context){for(const run of runs){const style=browserStyle(run.font,run.flags);context.font=`${style.fontStyle} ${style.fontWeight} ${run.size*zoom}px ${style.fontFamily}`;const lines=run.text.split('\n');for(let i=0;i<lines.length;i++){if(i){longest=Math.max(longest,line);line=0;}line+=context.measureText(lines[i]).width;}}longest=Math.max(longest,line);}
    setWidth(Math.max(40,Math.min((rotation?Math.max(pageWidth,pageHeight):pageWidth-draft.rect[0])*zoom-4,Math.max(rawWidth*zoom,longest+8))));
    element.style.height='auto';setHeight(Math.max(draft.size*zoom*1.35,element.scrollHeight));
  },[runs,width,zoom,pageWidth,pageHeight]);
  useEffect(()=>{const element=input.current;if(!element)return;undo.current=[];redo.current=[];element.focus();const selected=draft.selectedText?draft.text.indexOf(draft.selectedText):-1,caret=draft.caret??draft.text.length;savedSelection.current={start:selected>=0?selected:caret,end:selected>=0?selected+draft.selectedText!.length:caret};restoreSelection(element,savedSelection.current);},[draft.expected,draft.kind,draft.sourceRect.join(','),draft.point.join(',')]);
  return <>
    {draft.kind==='edit'&&<div className="inline-text-mask" style={{left:draft.rect[0]*zoom,top:draft.rect[1]*zoom,width:(draft.rect[2]-draft.rect[0])*zoom,height:(draft.rect[3]-draft.rect[1])*zoom}}/>}
    <div ref={input} className="inline-text-editor" role="textbox" aria-multiline="true" aria-label={draft.kind==='edit'?'Edit text on page':'New text on page'} aria-disabled={busy} contentEditable={!busy} suppressContentEditableWarning spellCheck={false} style={{left:x,top:y,width,height,fontSize:draft.size*zoom,color:draft.color,whiteSpace:'pre-wrap',overflowWrap:'break-word',transform:rotation?`rotate(${rotation}deg)`:undefined,transformOrigin:rotation?`${rawWidth*zoom/2}px ${(draft.sourceRect[3]-draft.sourceRect[1])*zoom/2}px`:undefined}} onInput={()=>{if(!composition.current)read();}} onCompositionStart={()=>{composition.current=true;}} onCompositionEnd={()=>{composition.current=false;read();}} onKeyUp={()=>{if(input.current)savedSelection.current=selectionIn(input.current);}} onMouseUp={()=>{if(input.current)savedSelection.current=selectionIn(input.current);}} onPaste={event=>{event.preventDefault();insert(event.clipboardData.getData('text/plain'));}} onKeyDown={event=>{
      if(busy||composition.current)return;
      if(event.key==='Escape'){event.preventDefault();onCancel();return;}
      if(event.key==='Enter'){event.preventDefault();if(event.ctrlKey||event.metaKey)onApply();else insert('\n');return;}
      if((event.ctrlKey||event.metaKey)&&['z','y'].includes(event.key.toLowerCase())){event.preventDefault();const reverse=event.key.toLowerCase()==='y'||event.shiftKey,source=reverse?redo:undo,target=reverse?undo:redo,next=source.current.pop();if(next){target.current.push(draft);onChange(next);}}
    }}/>
    <div className="inline-text-toolbar" style={{left:Math.min(draft.rect[0]*zoom,Math.max(0,pageWidth*zoom-420)),top:Math.max(0,draft.rect[1]*zoom-52)}}>
      <label>Font<select aria-label="Text font" disabled={busy} value={draft.font} onChange={event=>change({...draft,font:event.target.value})}>{fonts.filter(([value])=>value!=='original'||draft.kind==='edit').map(([value,label])=><option key={value} value={value}>{value==='original'?(draft.mixedStyles?'Original paragraph styles':`${label} (${draft.sourceFont})`):label}</option>)}</select></label>
      <label>Size<input aria-label="Text size" type="number" min="1" max="300" disabled={busy} value={draft.size} onChange={event=>change({...draft,size:Number(event.target.value)})}/></label><input aria-label="Text color" type="color" disabled={busy} value={draft.color} onChange={event=>change({...draft,color:event.target.value})}/><button disabled={busy||(draft.kind==='add'&&!draft.text.trim())} onClick={onApply}>Apply text</button><button disabled={busy} onClick={onCancel}>Cancel text</button>
    </div>
  </>;
}
