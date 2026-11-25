import type { FontResource } from './api';
export async function loadPreviewFonts(resources:FontResource[],signal?:AbortSignal,added?:(face:FontFace)=>void){
  const faces:FontFace[]=[],families:Record<string,string>={};
  let substitutes=0,compatible=0;
  for(const resource of resources){
    if(signal?.aborted)break;
    if(!['embedded','compatible'].includes(resource.status)||!resource.data||!resource.sha256){substitutes++;continue;}
    try{
      const bytes=Uint8Array.from(atob(resource.data),char=>char.charCodeAt(0));
      const family=`FolioPreview_${resource.sha256}_${resource.flags}`;
      const face=new FontFace(family,bytes,{weight:resource.flags&16?'700':'400',style:resource.flags&2?'italic':'normal'});
      await face.load();if(signal?.aborted)break;document.fonts.add(face);faces.push(face);if(resource.status==='compatible')compatible++;added?.(face);families[resource.name]=family;
    }catch{substitutes++;}
  }
  return {families,substitutes,compatible,dispose:()=>{for(const face of faces)document.fonts.delete(face);}};
}
