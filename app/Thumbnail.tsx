import { useEffect, useRef, useState } from 'react';
import { FileText } from 'lucide-react';
import { command, documentUrl, type DocumentInfo } from './api';
export function Thumbnail({document,page}:{document:DocumentInfo;page:number}) {
  const target=useRef<HTMLDivElement>(null);const [visible,setVisible]=useState(false);const [url,setUrl]=useState('');
  useEffect(()=>{const observer=new IntersectionObserver(entries=>{if(entries[0].isIntersecting){setVisible(true);observer.disconnect();}},{rootMargin:'100px'});if(target.current)observer.observe(target.current);return ()=>observer.disconnect();},[]);
  useEffect(()=>{if(!visible)return;let cancelled=false;command<{path:string}>('thumbnail',document,{page}).then(result=>{if(!cancelled)setUrl(documentUrl(result.path,document.revision));}).catch(()=>{});return ()=>{cancelled=true;};},[visible,document.revision,page,document.id]);
  return <div className="mini-page" ref={target}>{url?<img src={url} alt={`Page ${page} thumbnail`}/>:<FileText size={25}/>}<span>{page}</span></div>;
}
