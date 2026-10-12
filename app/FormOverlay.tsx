import type { CSSProperties } from 'react';
import type { PageInfo } from './api';

export function FormOverlay({fields,values,onChange,width,height,pageWidth,pageHeight,disabled}:{fields:PageInfo['forms'];values:Record<string,string|number>;onChange:(id:string,value:string|number)=>void;width:number;height:number;pageWidth:number;pageHeight:number;disabled:boolean}) {
  const scaleX=width/pageWidth,scaleY=height/pageHeight;
  return <div className="form-overlay" aria-label="On-page form fields">{fields.map(field=>{
    const supported=['Text','CheckBox','ComboBox','ListBox','RadioButton'].includes(field.type)&&!field.multi_select;
    if(!supported)return null;
    const value=values[field.id]??field.value??'';
    const raw=field.raw_rect||field.rect;
    const rotation=field.rotation||0;
    const controlWidth=(raw[2]-raw[0])*scaleX,controlHeight=(raw[3]-raw[1])*scaleY;
    const style:CSSProperties={width:controlWidth,height:controlHeight,transform:`translate(-50%, -50%) rotate(${rotation}deg)`,fontSize:Math.min(18,Math.max(8,controlHeight*.5))};
    const common={className:'form-control',style,disabled:disabled||field.read_only,'aria-label':field.type==='RadioButton'?`On-page ${field.name}: ${field.label||field.on_state}`:`On-page ${field.name}`,title:`${field.name}${field.read_only?' (read-only)':''}`};
    const on=field.states?.normal?.find(state=>state!=='Off')||'Yes';
    return <div className="form-widget" key={field.id} style={{left:field.rect[0]*scaleX,top:field.rect[1]*scaleY,width:(field.rect[2]-field.rect[0])*scaleX,height:(field.rect[3]-field.rect[1])*scaleY}}>
      {field.type==='RadioButton'?<input {...common} type="radio" name={`radio-${field.name}`} checked={value===field.on_state} onChange={()=>onChange(field.id,String(field.on_state))}/>:field.type==='CheckBox'?<input {...common} type="checkbox" checked={Boolean(value)&&value!=='Off'} onChange={event=>onChange(field.id,event.target.checked?on:'Off')}/>
      :field.choices?.length?<select {...common} size={field.type==='ListBox'?Math.max(2,Math.min(6,field.choices.length)):undefined} value={value} onChange={event=>onChange(field.id,event.target.value)}>{field.choices.map(choice=><option key={choice} value={choice}>{choice}</option>)}</select>
      :field.multiline?<textarea {...common} value={value} maxLength={field.max_length||undefined} onChange={event=>onChange(field.id,event.target.value)}/>
      :<input {...common} type={field.password?'password':'text'} value={value} maxLength={field.max_length||undefined} onChange={event=>onChange(field.id,event.target.value)}/>}
    </div>;
  })}</div>;
}
