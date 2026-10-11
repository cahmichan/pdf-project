export interface ArchivalResult {
  compliant:boolean;profile:string;statement:string;passed_rules:number;failed_rules:number;
  failures:string[];report:string;conversion_notes?:string;
}
export function ArchivalDialog({result,onClose,onSave}: {result:ArchivalResult;onClose:()=>void;onSave:()=>void}) {
  return <div className="modal-backdrop"><section className="modal signature-dialog" role="dialog" aria-label="Archival validation">
    <div className="section-heading"><h2>{result.compliant?'PDF/A-2b conformance passed':'PDF/A-2b conformance failed'}</h2><button onClick={onClose}>Close</button></div>
    <p>{result.statement}</p><dl className="archival-summary"><dt>Independent validator</dt><dd>veraPDF</dd><dt>Profile</dt><dd>{result.profile}</dd><dt>Rules passed</dt><dd>{result.passed_rules}</dd><dt>Rules failed</dt><dd>{result.failed_rules}</dd></dl>
    {!!result.failures.length&&<details open><summary>Failed checks</summary><ul>{result.failures.map((item,index)=><li key={index}>{item}</li>)}</ul></details>}
    {result.conversion_notes&&<details><summary>Conversion notes</summary><pre>{result.conversion_notes}</pre></details>}
    <p className="notice">Conformance checks document structure. Review the exported copy's text, colors and layout before relying on it. Archival conversion flattens forms and annotations and removes interactive links and attachments.</p>
    <button className="primary" onClick={onSave}>Save XML validation report</button>
  </section></div>;
}
