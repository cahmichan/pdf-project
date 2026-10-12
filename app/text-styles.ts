import type { TextRun } from './api';
import type { CSSProperties } from 'react';
type Match=[number,number,number];
// Match Python SequenceMatcher's no-junk longest-match ordering, including ties.
function matches(before:string[],after:string[]):Match[]{
  const positions=new Map<string,number[]>();after.forEach((char,index)=>{const list=positions.get(char)||[];list.push(index);positions.set(char,list);});
  const queue: number[][]=[[0,before.length,0,after.length]],blocks:Match[]=[];
  while(queue.length){
    const [lowA,highA,lowB,highB]=queue.pop()!;let bestA=lowA,bestB=lowB,size=0,previous=new Int32Array(after.length+1),current=new Int32Array(after.length+1);
    for(let i=lowA;i<highA;i++){
      current.fill(0);
      for(const j of positions.get(before[i])||[]){if(j<lowB)continue;if(j>=highB)break;const length=previous[j]+1;current[j+1]=length;if(length>size){bestA=i-length+1;bestB=j-length+1;size=length;}}
      [previous,current]=[current,previous];
    }
    if(size){blocks.push([bestA,bestB,size]);if(lowA<bestA&&lowB<bestB)queue.push([lowA,bestA,lowB,bestB]);if(bestA+size<highA&&bestB+size<highB)queue.push([bestA+size,highA,bestB+size,highB]);}
  }
  blocks.sort((a,b)=>a[0]-b[0]||a[1]-b[1]||a[2]-b[2]);
  const merged:Match[]=[];
  for(const block of blocks){const last=merged.at(-1);if(last&&last[0]+last[2]===block[0]&&last[1]+last[2]===block[1])last[2]+=block[2];else merged.push([...block]);}
  merged.push([before.length,after.length,0]);return merged;
}
export function liveRuns(before:string,source:TextRun[],after:string,size:number,sourceSize:number,color:string,sourceColor:string,colorMode:'auto'|'original'|'uniform'='auto'):TextRun[]{
  const old=Array.from(before),next=Array.from(after),styles=source.flatMap(run=>Array.from(run.text,()=>run));
  if(!styles.length||styles.length!==old.length)return [];
  const mapped:TextRun[]=before===after?[...styles]:[];let i=0,j=0;
  for(const [a,b,count] of before===after?[]:matches(old,next)){
    if(j<b){const inherited=a>i?styles[i]:styles[Math.max(0,i-1)];for(let k=j;k<b;k++)mapped.push(inherited);}
    mapped.push(...styles.slice(a,a+count));i=a+count;j=b+count;
  }
  const runs:TextRun[]=[];const ratio=size/sourceSize,override=colorMode==='uniform'||(colorMode==='auto'&&color.toLowerCase()!==sourceColor.toLowerCase());
  next.forEach((char,index)=>{const style=mapped[index],run={...style,text:char,size:style.size*ratio,offset:style.offset*ratio,color:override?color:style.color};const last=runs.at(-1);if(last&&last.font===run.font&&last.size===run.size&&last.color===run.color&&last.flags===run.flags&&last.offset===run.offset)last.text+=char;else runs.push(run);});
  return runs;
}
export function browserStyle(font:string,flags:number):CSSProperties{
  const serif=!!(flags&4)||/times|serif|^ti/i.test(font),mono=!!(flags&8)||/courier|mono|^co/i.test(font);
  return {fontFamily:mono?'Courier New, monospace':serif?'Times New Roman, serif':'Arial, sans-serif',fontWeight:flags&16||/bold|hebo|tibo|cobo/.test(font)?'bold':'normal',fontStyle:flags&2||/italic|oblique|heit|tiit|coit/.test(font)?'italic':'normal'};
}
