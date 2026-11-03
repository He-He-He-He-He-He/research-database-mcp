/** 全国报刊索引：通过已认证的 CUA 页面进行一次普通检索，返回首屏题录。 */
export async function searchCNBKSY(tab,keyword){
 if(typeof keyword!=='string'||!keyword.trim()||keyword.length>100||/[\r\n]/.test(keyword))throw new Error('关键词需为1–100字单行文本');
 const query=keyword.trim();
 const state=await tab.getAXState({emit:false,disableDiffing:true});
 if(!state.includes('cnbksy.com/v2/'))throw new Error('请绑定全国报刊索引新版页面');
 const cdp=await tab.capabilities.get('cdp');await cdp.send('Network.enable');let cursor=(await cdp.readEvents()).cursor;
 await tab.playwright.locator('#imgSearch').fill(query);
 await tab.playwright.getByRole('button',{name:'搜索',exact:true}).click();
 let id=null;
 for(let i=0;i<12;i++){
  const batch=await cdp.readEvents({afterSequence:cursor,methods:['Network.requestWillBeSent','Network.responseReceived'],timeoutMs:3000,limit:100});cursor=batch.cursor;
  if(batch.truncated)throw new Error('事件已截断，无法验证检索');
  for(const e of batch.events){
   if(e.method==='Network.requestWillBeSent'){
    const req=e.params?.request;if(!req?.url||req.method!=='POST')continue;
    let u;try{u=new URL(req.url)}catch{continue}
    if(u.origin!=='https://www.cnbksy.com'||u.pathname!=='/api/v2/search/query')continue;
    let payload;try{payload=JSON.parse(req.postData||'{}')}catch{continue}
    if(payload.searchContent===query && payload.pageNumber===0)id=e.params.requestId;
   }
   if(e.method==='Network.responseReceived'&&id&&e.params?.requestId===id){
    if(e.params.response.status!==200)throw new Error('检索失败：HTTP '+e.params.response.status);
    const response=await cdp.send('Network.getResponseBody',{requestId:id});
    if(response.base64Encoded)throw new Error('暂不支持此响应编码');
    let data;try{data=JSON.parse(response.body)}catch{throw new Error('上游未返回 JSON，请检查登录状态')}
    if(data.code!==200||!Array.isArray(data.data))throw new Error('检索结果异常或权限不足');
    return {query,source:'全国报刊索引普通检索',note:'混合文献类型；结果含正文、图片和广告分类，不能将总量等同近代报纸。',groups:data.data};
   }
  }
 }
 throw new Error('未观察到本次成功响应，请检查认证或网站状态');
}
