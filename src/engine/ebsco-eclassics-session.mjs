/** EBSCO eClassics 只读首屏检索；需 CUA 已验证机构权限并且选中 eClassics。 */
export async function searchEbscoEClassics(tab,keyword){
 if(typeof keyword!=='string'||!keyword.trim()||keyword.length>100||/[\r\n]/.test(keyword))throw new Error('关键词需为1–100字单行文本');
 const query=keyword.trim();
 const state=await tab.getAXState({emit:false,disableDiffing:true});
 if(!state.includes('research.ebsco.com/')||!state.includes('EBSCO eClassics Collection'))throw new Error('请绑定已选中 EBSCO eClassics Collection 的馆藏页面');
 const cdp=await tab.capabilities.get('cdp');await cdp.send('Network.enable');let cursor=(await cdp.readEvents()).cursor;
 await tab.playwright.locator('#search-input').fill(query);
 await tab.playwright.getByRole('button',{name:'搜索',exact:true}).click();
 let id=null;
 for(let i=0;i<12;i++){
  const batch=await cdp.readEvents({afterSequence:cursor,methods:['Network.requestWillBeSent','Network.responseReceived'],timeoutMs:3000,limit:100});cursor=batch.cursor;
  if(batch.truncated)throw new Error('事件记录截断，不能核验');
  for(const e of batch.events){
   if(e.method==='Network.requestWillBeSent'){
    const req=e.params?.request;if(!req?.url||req.method!=='POST')continue;
    let u;try{u=new URL(req.url)}catch{continue}
    if(u.origin!=='https://research.ebsco.com'||u.pathname!=='/api/search/v1/search')continue;
    let p;try{p=JSON.parse(req.postData||'{}')}catch{continue}
    if(p.query===query && p.offset===0 && p.filters?.some(f=>f.id==='databases'&&f.values?.includes('e63sww')))id=e.params.requestId;
   }
   if(e.method==='Network.responseReceived'&&id&&e.params?.requestId===id){
    if(e.params.response.status!==200)throw new Error('检索失败：HTTP '+e.params.response.status);
    const r=await cdp.send('Network.getResponseBody',{requestId:id});if(r.base64Encoded)throw new Error('暂不支持响应编码');
    let data;try{data=JSON.parse(r.body)}catch{throw new Error('返回非 JSON，可能需要登录')}
    if(!Array.isArray(data.search?.items))throw new Error('检索返回结构异常');
    return {query,source:'EBSCO eClassics Collection',total:data.search.totalItems,items:data.search.items};
   }
  }
 }
 throw new Error('未观察到目标馆藏的本次成功响应，请检查会话');
}
