import { useState } from 'react';
import { Thumbnail } from './Thumbnail';
import type { DocumentInfo } from './api';

interface Entry { key:string; page:number }
export function PageOrganizer({document,onClose,onApply}:{document:DocumentInfo;onClose:()=>void;onApply:(pages:number[])=>Promise<boolean>}) {
  const original=()=>document.pages.map((_,index)=>({key:crypto.randomUUID(),page:index+1}));
  const [entries,setEntries]=useState<Entry[]>(original);
  const [selected,setSelected]=useState(0);
  const [dragged,setDragged]=useState<string|null>(null);
  const [busy,setBusy]=useState(false);
  const [error,setError]=useState('');
  const changed=entries.length!==document.page_count||entries.some((entry,index)=>entry.page!==index+1);
  function move(from:number,to:number) {
    if(from<0||to<0||from>=entries.length||to>=entries.length||busy)return;
    setEntries(previous=>{const next=[...previous];next.splice(to,0,next.splice(from,1)[0]);return next;});
    setSelected(to);
  }
  async function apply() {
    setBusy(true);setError('');
    try{if(await onApply(entries.map(entry=>entry.page)))onClose();}
    catch(reason){setError(String(reason).replace(/^Error: /,''));}
    finally{setBusy(false);}
  }
  return <div className="modal-backdrop"><section className="modal organizer-dialog" role="dialog" aria-modal="true" aria-label="Organize pages">
    <div className="section-heading"><h2>Organize pages</h2><button disabled={busy} onClick={onClose}>Cancel</button></div>
    <p>Drag a page to move it, or select a page and use the controls. Changes apply together and can be undone.</p>
    <div className="organizer-controls">
      <button disabled={busy||selected===0} onClick={()=>move(selected,selected-1)}>Move left</button>
      <button disabled={busy||selected===entries.length-1} onClick={()=>move(selected,selected+1)}>Move right</button>
      <button disabled={busy} onClick={()=>{const copy={key:crypto.randomUUID(),page:entries[selected].page};setEntries(previous=>[...previous.slice(0,selected+1),copy,...previous.slice(selected+1)]);setSelected(selected+1);}}>Duplicate selected</button>
      <button disabled={busy||entries.length===1} onClick={()=>{setEntries(previous=>previous.filter((_,index)=>index!==selected));setSelected(Math.min(selected,entries.length-2));}}>Remove selected</button>
      <button disabled={busy||!changed} onClick={()=>{setEntries(original());setSelected(0);}}>Reset order</button>
    </div>
    <div className="organizer-grid" aria-label="Staged page order">{entries.map((entry,index)=><button
      key={entry.key} className={`organizer-page ${selected===index?'selected':''}`} disabled={busy}
      aria-label={`Position ${index+1}, source page ${entry.page}`} aria-pressed={selected===index}
      draggable={!busy} onClick={()=>setSelected(index)}
      onDragStart={event=>{setDragged(entry.key);event.dataTransfer.setData('text/plain',entry.key);event.dataTransfer.effectAllowed='move';}}
      onDragEnd={()=>setDragged(null)} onDragOver={event=>{event.preventDefault();event.dataTransfer.dropEffect='move';}}
      onDrop={event=>{event.preventDefault();const key=dragged||event.dataTransfer.getData('text/plain');move(entries.findIndex(item=>item.key===key),index);setDragged(null);}}>
      <Thumbnail document={document} page={entry.page}/><strong>Position {index+1}</strong><small>Source page {entry.page}</small>
    </button>)}</div>
    <p aria-live="polite">{entries.length} pages in the proposed document. {changed?'Changes ready to apply.':'No changes yet.'}</p>
    {entries.some((entry,index)=>entries.findIndex(item=>item.page===entry.page)!==index)&&<p className="notice">Copies can be edited independently. Copied form fields receive distinct names; internal links target the first retained copy of their destination.</p>}
    {error&&<p role="alert" className="notice warning">{error}</p>}
    <button className="primary" disabled={busy||!changed} onClick={()=>void apply()}>{busy?'Applying…':'Apply page order'}</button>
  </section></div>;
}
