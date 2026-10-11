import { useEffect, useState } from 'react';
import { command, type DocumentInfo } from './api';

interface Inspection {
  signatures:{field:string;signer?:string;intact?:boolean;valid?:boolean;trusted?:boolean;coverage?:string;modification?:string;docmdp_ok?:boolean;details?:string;error?:string}[];
  offline:boolean;explicit_trust_roots:number;note:string;
}
export function SignatureDialog({document,initialTab,onClose,chooseFile,chooseOutput,onOpen}: {
  document:DocumentInfo;initialTab:string;onClose:()=>void;
  chooseFile:(extensions:string[])=>Promise<string[]|null>;
  chooseOutput:(name:string,extension:string)=>Promise<string|null>;
  onOpen:(path:string)=>void;
}) {
  const [tab,setTab]=useState(initialTab);const [identity,setIdentity]=useState('');
  const [password,setPassword]=useState('');const [name,setName]=useState('');const [reason,setReason]=useState('');
  const [trust,setTrust]=useState('');const [result,setResult]=useState<Inspection|null>(null);
  const [signed,setSigned]=useState('');const [busy,setBusy]=useState(false);const [error,setError]=useState('');const [message,setMessage]=useState('');
  async function run(action:()=>Promise<void>){setBusy(true);setError('');setMessage('');try{await action();}catch(e){setError(String(e).replace(/^Error: /,''));}finally{setPassword('');setBusy(false);}}
  async function inspect(){await run(async()=>setResult(await command<Inspection>('inspect_signatures',document,{trust_path:trust||undefined})));}
  useEffect(()=>{if(initialTab==='inspect')void inspect();},[]);
  async function sign(){await run(async()=>{
    if(!identity)throw new Error('Choose a local signing identity first.');
    const path=await chooseOutput(document.name.replace(/\.pdf$/i,'')+'-signed.pdf','pdf');if(!path)return;
    const output=await command<{path:string;validation:Inspection}>('sign_copy',document,{path,identity,password,reason,overwrite:true});
    setSigned(output.path);setResult(output.validation);setMessage('Signed copy saved. The current working document remains unchanged.');
  });}
  async function create(){await run(async()=>{
    const path=await chooseOutput('personal-identity.pfx','pfx');if(!path)return;
    const output=await command<{path:string;note:string}>('create_identity',null,{path,name,password});
    setIdentity(output.path);setMessage(output.note+' Keep this file and its password safe.');setTab('sign');
  });}
  async function exportCertificate(){await run(async()=>{
    const path=await chooseOutput('personal-certificate.pem','pem');if(!path)return;
    const output=await command<{path:string}>('export_certificate',null,{path,identity,password});
    setTrust(output.path);setMessage('Public certificate exported. It contains no private key. Select Inspect signatures to validate using this certificate.');
  });}
  return <div className="modal-backdrop"><section className="modal signature-dialog" role="dialog" aria-label="Certificate signatures">
    <div className="section-heading"><h2>Certificate signatures</h2><button disabled={busy} onClick={onClose}>Close</button></div>
    <div className="signature-tabs">{[['sign','Sign a copy'],['inspect','Inspect signatures'],['identity','Create personal identity']].map(([id,label])=><button key={id} disabled={busy} className={tab===id?'primary':''} onClick={()=>{setTab(id);setPassword('');}}>{label}</button>)}</div>
    {error&&<p role="alert" className="error-banner">{error}</p>}{message&&<p className="notice">{message}</p>}
    {tab==='sign'&&<><p>A certificate signature detects changes to signed bytes. Choose a local PKCS#12 identity; the result is a separate PDF.</p><label>Signing identity<input readOnly value={identity} placeholder="Choose a .pfx or .p12 file"/></label><button disabled={busy} onClick={async()=>{const files=await chooseFile(['pfx','p12']);if(files)setIdentity(files[0]);}}>Choose signing identity</button><label>Identity password<input type="password" autoComplete="off" value={password} onChange={e=>setPassword(e.target.value)}/></label><label>Reason (optional)<input value={reason} onChange={e=>setReason(e.target.value)}/></label><button className="primary" disabled={busy||!identity} onClick={()=>void sign()}>Save signed PDF</button><button disabled={busy||!identity} onClick={()=>void exportCertificate()}>Export public certificate</button>{signed&&<button disabled={busy} onClick={()=>onOpen(signed)}>Open signed copy</button>}</>}
    {tab==='identity'&&<><p>Create a free self-signed identity for personal documents. Other readers will need to explicitly trust its certificate. Folio does not add it to Windows trust stores.</p><label>Certificate name<input value={name} onChange={e=>setName(e.target.value)} maxLength={100}/></label><label>New identity password<input type="password" autoComplete="new-password" value={password} onChange={e=>setPassword(e.target.value)}/><small>At least 8 characters. Passwords are not saved by Folio.</small></label><button className="primary" disabled={busy||!name.trim()||password.length<8} onClick={()=>void create()}>Create identity file</button></>}
    {tab==='inspect'&&<><label>Explicit trust certificate (optional)<input readOnly value={trust} placeholder="No trusted certificates selected"/></label><div className="signature-tabs"><button disabled={busy} onClick={async()=>{const files=await chooseFile(['pem','crt','cer','der']);if(files)setTrust(files[0]);}}>Choose trust certificate</button><button disabled={busy||!trust} onClick={()=>setTrust('')}>Clear trust</button><button disabled={busy} className="primary" onClick={()=>void inspect()}>Inspect current PDF</button></div></>}
    {busy&&<p role="status">Working locally…</p>}
    {result&&<div className="signature-results">{!result.signatures.length&&<p>No certificate signatures found in this working PDF.</p>}{result.signatures.map(item=><article key={item.field}><strong>{item.signer||item.field}</strong><small>{item.field}</small>{item.error?<p role="alert">{item.error}</p>:<><dl><dt>Signed bytes intact</dt><dd>{item.intact?'Yes':'No'}</dd><dt>Cryptographic signature valid</dt><dd>{item.valid?'Yes':'No'}</dd><dt>Certificate trusted in this inspection</dt><dd>{item.trusted?'Yes':'No'}</dd><dt>Coverage</dt><dd>{item.coverage}</dd><dt>Later modifications</dt><dd>{item.modification}</dd><dt>Document permissions respected</dt><dd>{item.docmdp_ok?'Yes':'No'}</dd></dl><details><summary>Validation details</summary><pre>{item.details}</pre></details></>}</article>)}</div>}
    <p className="notice">Offline inspection does not establish current revocation status or a trusted signing time. A self-signed identity is not automatically trusted. Certificate signing is distinct from a signature image.</p>
  </section></div>;
}
