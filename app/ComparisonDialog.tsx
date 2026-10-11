import { documentUrl } from './api';
export interface ComparisonResult {
  left_pages:number;right_pages:number;changed_pages:number;report:string;note:string;
  pages:{page:number;changed:boolean;pixel_ratio:number;dimensions_changed:boolean;text_diff:string;image:string|null}[];
}
export function ComparisonDialog({result,onClose,onSave}:{result:ComparisonResult;onClose:()=>void;onSave:()=>void}) {
  return <div className="modal-backdrop"><section className="comparison-dialog" role="dialog" aria-modal="true" aria-label="PDF comparison">
    <div className="section-heading"><h2>{result.changed_pages} changed pages</h2><div><button onClick={onSave}>Save HTML report</button><button onClick={onClose}>Close</button></div></div>
    <p>Current PDF: {result.left_pages} pages · Other PDF: {result.right_pages} pages</p><p className="notice">{result.note}</p>
    {result.pages.filter(item=>item.changed).map(item=><article key={item.page}><h3>Page {item.page}</h3><p>{(item.pixel_ratio*100).toFixed(2)}% of pixels changed{item.dimensions_changed?' · Different page dimensions':''}</p>{item.text_diff&&<pre>{item.text_diff}</pre>}{item.image&&<img loading="lazy" src={documentUrl(item.image,0)} alt={`Page ${item.page}: differences marked in pink`}/>}</article>)}
    {!result.changed_pages&&<p>No changes detected at the comparison resolution.</p>}
  </section></div>;
}
