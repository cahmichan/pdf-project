import net from 'node:net';
import { execFileSync } from 'node:child_process';
export async function debugPort(){
  const server=net.createServer();await new Promise((resolve,reject)=>{server.once('error',reject);server.listen(0,'127.0.0.1',resolve);});
  const port=server.address().port;await new Promise(resolve=>server.close(resolve));return port;
}
export function stopNative(child){
  if(child.exitCode!==null)return;
  try{execFileSync('taskkill',['/PID',String(child.pid),'/T','/F'],{windowsHide:true,stdio:'pipe'});}catch{child.kill();}
}
