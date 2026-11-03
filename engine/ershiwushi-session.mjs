/** 二十五史研习系统单次关键词检索：读取实际网页 HTML 查询响应，返回分类命中数。 */
export async function searchErShiWuShi(tab,keyword){
 if(typeof keyword!=='string'||!keyword.trim()||keyword.length>80||/[\r\n]/.test(keyword))throw new Error('关键词须为1–80字的单行文本');
 const query=keyword.trim();
 const state=await tab.getAXState({emit:false,disableDiffing:true});
 if(!state.includes('chinabooktrading.com:81/h25/'))throw new Error('请绑定二十五史研习系统工作页');
 const cdp=await tab.capabilities.get('cdp');await cdp.send('Network.enable');let cursor=(await cdp.readEvents()).cursor;
 await tab.goto('http://www.chinabooktrading.com:81/h25/QUERY/'+encodeURIComponent(query));
 let id=null, accepted=false;
 for(let i=0;i<12;i++){
  const batch=await cdp.readEvents({afterSequence:cursor,methods:['Network.requestWillBeSent','Network.responseReceived','Network.loadingFinished'],timeoutMs:3000,limit:100});cursor=batch.cursor;
  if(batch.truncated)throw new Error('事件已截断');
  for(const e of batch.events){
   if(e.method==='Network.requestWillBeSent'){
    const req=e.params?.request;if(!req?.url||req.method!=='GET')continue;
    let u;try{u=new URL(req.url)}catch{continue}
    let path;try{path=decodeURIComponent(u.pathname)}catch{continue}
    if(u.hostname==='www.chinabooktrading.com'&&u.port==='81'&&path==='/h25/QUERY/'+query)id=e.params.requestId;
   }
   if(e.method==='Network.responseReceived'&&id&&e.params?.requestId===id){
    if(e.params.response.status!==200)throw new Error('检索失败：HTTP '+e.params.response.status);
    accepted=true;
   }
   if(e.method==='Network.loadingFinished'&&id&&accepted&&e.params?.requestId===id){
    const response=await cdp.send('Network.getResponseBody',{requestId:id});if(response.base64Encoded)throw new Error('暂不支持响应编码');
    const block=response.body.match(/<ul\s+class="data"[^>]*>([\s\S]*?)<\/ul>/i);
    if(!block)throw new Error('未找到结果分类，可能页面或授权已变化');
    const groups=[];
    for(const m of block[1].matchAll(/<li>\s*<a\s+href="([^"]*)"[^>]*>[\s\S]*?<em\s+class="dir">([^<]*)<\/em>[\s\S]*?<em\s+class="count">(\d+)<\/em>[\s\S]*?<\/a>\s*<\/li>/gi))groups.push({path:m[2].trim(),count:Number(m[3])});
    if(block[1].includes('<li>')&&groups.length===0)throw new Error('结果格式变化，不能识别分类');
    return {query,source:'二十五史研习系统查询响应',groups,note:'结果包括正史、其他文献及知识库分类；上游使用 HTTP。仅返回分类数量，不获取全文。'};
   }
  }
 }
 throw new Error('未观察到查询响应');
}
