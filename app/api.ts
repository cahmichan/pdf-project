import { invoke, convertFileSrc, isTauri } from '@tauri-apps/api/core';
export interface DocumentInfo {
  id: string; name: string; source: string | null; path: string; revision: number;
  dirty: boolean; page_count: number; can_undo: boolean; can_redo: boolean;
  signature_fields: boolean; metadata: Record<string,string>;
  bookmarks: [number,string,number][];
  ocr_report?:{pages_processed:number;pages_skipped:number;words_added:number};
  pages: {width:number;height:number;rotation:number;cropbox:number[]}[];
}
export interface PageInfo {
  text: string; blocks: {rect:number[];text:string;size:number}[];
  text_blocks?:TextBlock[];
  forms: {id:string;name:string;type:string;value:string|number;rect:number[];label?:string;on_state?:string|boolean|null;raw_rect?:number[];rotation?:number;read_only?:boolean;multiline?:boolean;password?:boolean;multi_select?:boolean;max_length?:number;choices?:string[];states?:{normal?:string[]}}[];
  annotations: {id:number;type:string;rect:number[];content:string}[];
  images: {id:number;rect:number[];width:number;height:number}[];
  links: {rect:number[];page:number;uri:string}[];
}
export interface TextRun {text:string;font:string;size:number;color:string;flags:number;offset:number;}
export interface FontResource {name:string;flags:number;status:'embedded'|'compatible'|'substitute';reason?:string;format?:string;sha256?:string;data?:string;}
export interface TextBlock {id:number;text:string;rect:number[];raw_rect:number[];size:number;font:string;flags:number;color:string;rotation:number;horizontal:boolean;origin:number[];mixed_styles:boolean;runs?:TextRun[];}
let sequence = 0;
export async function command<T>(name: string, document?: DocumentInfo | null, args: Record<string,unknown> = {}): Promise<T> {
  const request = {command:name, session:document?.id, revision:document?.revision, args, job:++sequence};
  if (isTauri()) return invoke<T>('pdf_command', {request});
  // Development-only bridge; never bundled as a network service in desktop releases.
  const response = await fetch('/api/pdf', {method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(request)});
  const result = await response.json();
  if (!result.ok) throw new Error(result.error.message);
  return result.result as T;
}
export function documentUrl(path: string, revision: number) {
  return isTauri() ? `${convertFileSrc(path)}?revision=${revision}` : `/api/document?path=${encodeURIComponent(path)}&revision=${revision}`;
}
export async function cancelWorker() {
  if (isTauri()) await invoke('pdf_cancel');
}
