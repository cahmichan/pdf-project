import { useState } from 'react';
import { isTauri } from '@tauri-apps/api/core';
import { cancelWorker } from './api';
export interface SplitResult {manifest:string;items:{pages:number[];status:string;output?:string;error?:string}[]}
export function SplitDialog({count,onClose,chooseFolder,onRun,onOpen}:{count:number;onClose:()=>void;chooseFolder:()=>Promise<string|null>;onRun:(args:Record<string,unknown>)=>Promise<SplitResult|null>;onOpen:(path:string)=>void}) {
  const [mode,setMode]=useState('individual');const [size,setSize]=useState(1);const [ranges,setRanges]=useState('');
  const [folder,setFolder]=useState('');const [busy,setBusy]=useState(false);const [error,setError]=useState('');const [result,setResult]=useState<SplitResult|null>(null);
  async function run(){setBusy(true);setError('');setResult(null);try{setResult(await onRun({mode,size,ranges,folder}));}catch(reason){setError(String(reason).replace(/^Error: /,''));}finally{setBusy(false);}}
  return <div className="modal-backdrop"><section className="modal signature-dialog" role="dialog" aria-modal="true" aria-label="Split PDF">
    <div className="section-heading"><h2>Split PDF</h2><button disabled={busy} onClick={onClose}>Close</button></div>
    <p>Save separate PDF files from this {count}-page working document. Every output gets a new name; your working document stays intact.</p>
    <label>Split method<select aria-label="Split method" value={mode} disabled={busy} onChange={event=>setMode(event.target.value)}><option value="individual">One file per page</option><option value="every">Pages per file</option><option value="ranges">Custom page groups</option></select></label>
    {mode==='every'&&<label>Pages per file<input aria-label="Pages per file" type="number" min={1} max={count} step={1} value={size} disabled={busy} onChange={event=>setSize(Number(event.target.value))}/><small>The final file includes any remaining pages.</small></label>}
    {mode==='ranges'&&<label>Page groups<input aria-label="Page groups" placeholder="1-3;4-6;7,9" value={ranges} disabled={busy} onChange={event=>setRanges(event.target.value)}/><small>Separate files with semicolons. Pages can overlap or appear in a different order.</small></label>}
    <button disabled={busy} onClick={async()=>{try{const chosen=await chooseFolder();if(chosen)setFolder(chosen);}catch(reason){setError(String(reason));}}}>Choose split output folder</button>
    {folder&&<p className="batch-path">{folder}</p>}
    {error&&<p role="alert" className="notice warning">{error}</p>}
    <button className="primary" disabled={busy||!folder||(mode==='every'&&(!Number.isInteger(size)||size<1))||(mode==='ranges'&&!ranges.trim())} onClick={()=>void run()}>{busy?'Splitting…':'Save split PDFs'}</button>{busy&&isTauri()&&<button onClick={()=>void cancelWorker().catch(reason=>setError(String(reason)))}>Stop worker</button>}
    {result&&<><h3>{result.items.filter(item=>item.status==='done').length} of {result.items.length} files saved</h3><p className="batch-path">Receipt: {result.manifest}</p><div className="split-results">{result.items.map((item,index)=><article key={index}><strong>Part {index+1} · {item.pages.length} pages</strong><p className="batch-path">{item.output||item.error||item.status}</p>{item.output&&<button onClick={()=>onOpen(item.output!)}>Open part {index+1}</button>}</article>)}</div></>}
  </section></div>;
}
