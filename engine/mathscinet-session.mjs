/** MathSciNet 馆方网页只读查询，需使用已具机构访问权限的 CUA 标签。 */
export async function searchMathSciNet(tab,keyword){
 if(typeof keyword!=='string'||!keyword.trim()||keyword.length>100||/[\r\n]/.test(keyword)) throw new Error('关键词需为1–100字单行文本');
 const query=keyword.trim();
 const state=await tab.getAXState({emit:false,disableDiffing:true});
 if(!state.includes('mathscinet.ams.org/mathscinet/')) throw new Error('请绑定 MathSciNet 检索页面');
 const cdp=await tab.capabilities.get('cdp');await cdp.send('Network.enable');let cursor=(await cdp.readEvents()).cursor;
 await tab.playwright.locator('#searchTextInput').fill(query);
 await tab.playwright.getByRole('button',{name:'Search',exact:true}).click();
 let id=null;
 for(let i=0;i<12;i++){
  const batch=await cdp.readEvents({afterSequence:cursor,methods:['Network.requestWillBeSent','Network.responseReceived'],timeoutMs:3000,limit:100});cursor=batch.cursor;
  if(batch.truncated)throw new Error('事件截断，无法核验查询');
  for(const e of batch.events){
   if(e.method==='Network.requestWillBeSent'){
    const req=e.params?.request;if(!req?.url||req.method!=='GET')continue;
    let u;try{u=new URL(req.url)}catch{continue}
    if(u.origin==='https://mathscinet.ams.org'&&u.pathname.replace(/\/{2,}/g,'/')==='/mathscinet/api/publications/search'&&u.searchParams.get('query')===query)id=e.params.requestId;
   }
   if(e.method==='Network.responseReceived'&&id&&e.params?.requestId===id){
    if(e.params.response.status!==200)throw new Error('检索失败：HTTP '+e.params.response.status);
    const response=await cdp.send('Network.getResponseBody',{requestId:id});
    if(response.base64Encoded)throw new Error('暂不支持此响应编码');
    let data;try{data=JSON.parse(response.body)}catch{throw new Error('未返回 JSON，检查登录或授权')}
    if(!Array.isArray(data.results)||typeof data.total!=='number')throw new Error('返回结构异常');
    return {query,source:'MathSciNet Publications',total:data.total,items:data.results};
   }
  }
 }
 throw new Error('未观察到成功的查询响应，请检查授权或站点状态');
}
