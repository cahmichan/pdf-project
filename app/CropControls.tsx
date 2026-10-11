export type CropMargins=Record<'left'|'top'|'right'|'bottom',number>;
export function CropControls({mode,onMode,margins,onMargins,unit,onUnit,width,height,selection}:{mode:string;onMode:(value:string)=>void;margins:CropMargins;onMargins:(value:CropMargins)=>void;unit:string;onUnit:(value:string)=>void;width:number;height:number;selection:number[]|null}) {
  const factor=unit==='mm'?72/25.4:unit==='in'?72:1;
  const display=(value:number)=>Math.round(value/factor*1000)/1000;
  const newWidth=mode==='selection'&&selection?selection[2]-selection[0]:width-margins.left-margins.right;
  const newHeight=mode==='selection'&&selection?selection[3]-selection[1]:height-margins.top-margins.bottom;
  return <>
    <label>Crop method<select aria-label="Crop method" value={mode} onChange={event=>onMode(event.target.value)}><option value="margins">Trim margins</option><option value="selection">Draw a rectangle</option><option value="reset">Reset to full page</option></select></label>
    <label>Crop units<select aria-label="Crop units" value={unit} onChange={event=>onUnit(event.target.value)}><option value="pt">Points</option><option value="mm">Millimeters</option><option value="in">Inches</option></select></label>
    {mode==='margins'&&<div className="crop-margins">{(['top','left','right','bottom'] as const).map(edge=><label key={edge}>{edge[0].toUpperCase()+edge.slice(1)} ({unit})<input aria-label={`Crop ${edge}`} type="number" min={0} step="any" value={display(margins[edge])} onChange={event=>onMargins({...margins,[edge]:Number(event.target.value)*factor})}/></label>)}</div>}
    {mode==='selection'&&<p className="notice">Drag a rectangle to keep on the current page. This applies only to the current page.{!selection&&' Choose a rectangle before applying.'}</p>}
    {mode!=='reset'&&<p className="notice" aria-live="polite">Current page after crop: {display(newWidth)} × {display(newHeight)} {unit}.{newWidth<=0||newHeight<=0?' Reduce the margins to retain a visible area.':''}</p>}
    {mode==='reset'&&<p className="notice">Restore the full physical page for the chosen page range. Previously hidden margins become visible.</p>}
    <p className="notice">Margins follow the page as displayed, including its rotation. Cropping hides content; use redaction to remove sensitive content.</p>
  </>;
}
