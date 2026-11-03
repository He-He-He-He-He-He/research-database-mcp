/** Cairn 单次 HTML 响应型题录检索，需 CUA 工作标签；原始响应只在内存/管道中处理。 */
import {execFile} from 'node:child_process';
import {fileURLToPath} from 'node:url';
import {dirname,join} from 'node:path';
const parser=join(dirname(fileURLToPath(import.meta.url)),'cairn_response_parse.py');
function parse(html){return new Promise((resolve,reject)=>{
 const child=execFile('/usr/bin/python3',[parser],{maxBuffer:4*1024*1024,timeout:10000},(err,out)=>{if(err)return reject(new Error('HTML 解析失败'));try{resolve(JSON.parse(out))}catch{reject(new Error('题录解析结果异常'))}});
 child.stdin.on('error',()=>{});child.stdin.end(html);
});}
export async function searchCairnResponse(tab,keyword){
 if(typeof keyword!=='string'||!keyword.trim()||keyword.length>100||/[\r\n]/.test(keyword))throw new Error('关键词需为 1–100 字单行文本');
 const query=keyword.trim();const initial=await tab.getAXState({emit:false,disableDiffing:true});
 if(!initial.includes('shs.cairn.info/'))throw new Error('请绑定 Cairn 工作标签');
 const cdp=await tab.capabilities.get('cdp');await cdp.send('Network.enable');let cursor=(await cdp.readEvents()).cursor;
 await tab.goto('https://shs.cairn.info/recherche?lang=fr&term='+encodeURIComponent(query));
 let id=null;
 for(let i=0;i<12;i++){
  const batch=await cdp.readEvents({afterSequence:cursor,methods:['Network.requestWillBeSent','Network.responseReceived'],timeoutMs:3000,limit:500});cursor=batch.cursor;
  if(batch.truncated)throw new Error('浏览器响应记录截断');
  for(const e of batch.events){
   if(e.method==='Network.requestWillBeSent'){
    const req=e.params?.request;if(!req?.url||req.method!=='GET')continue;
    let u;try{u=new URL(req.url)}catch{continue}
    if(u.origin==='https://shs.cairn.info'&&u.pathname==='/recherche'&&u.searchParams.get('term')===query)id=e.params.requestId;
   }
   if(e.method==='Network.responseReceived'&&id&&e.params?.requestId===id){
    if(e.params.response.status!==200)throw new Error('Cairn 检索失败：HTTP '+e.params.response.status);
    const r=await cdp.send('Network.getResponseBody',{requestId:id});if(r.base64Encoded)throw new Error('响应编码暂不支持');
    const result=await parse(r.body);
    if(!result.heading.includes(query)||result.total===null)throw new Error('响应不含可识别的查询题录');
    return {query,source:'Cairn.info 检索页面 HTML 响应',total:result.total,items:result.items,note:'首屏题录，机构与全文权限未核验。'};
   }
  }
 }
 throw new Error('未观察到本次查询响应');
}
