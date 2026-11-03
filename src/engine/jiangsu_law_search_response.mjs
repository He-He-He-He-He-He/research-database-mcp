/** 捕获用户正常浏览器操作产生的江苏人大法规库搜索响应，不重放请求。 */
export function validateJiangsuCategory(x){const v=x?.list;if(!v||!Array.isArray(v.records)||!Number.isSafeInteger(v.total)||v.total<0||v.records.length>10||v.records.length>v.total)throw Error('分类搜索结构或总数异常')}
export async function jiangsuLawSearchResponse(tab, query, submitSearch) {
  if (typeof query !== 'string' || !query.trim() || query.length > 100 || typeof submitSearch !== 'function') throw Error('需要 1–100 字关键词及提交搜索回调');
  const q=query.trim(), c=await tab.capabilities.get('cdp'); await c.send('Network.enable');
  const methods=['Network.requestWillBeSent','Network.responseReceived','Network.loadingFinished']; let cursor=(await c.readEvents({methods})).cursor;
  await submitSearch(); const ids=new Set(), ok=new Set(), done=new Set();
  for (const deadline=Date.now()+25000;Date.now()<deadline;) {
    const e=await c.readEvents({afterSequence:cursor,methods,limit:1000,timeoutMs:1000});cursor=e.cursor;if(e.truncated)throw Error('搜索网络事件不完整');
    for (const x of e.events) {
      const p=x.params||{};
      if(x.method==='Network.requestWillBeSent' && p.request?.method==='POST') {
        let u,body;try {u=new URL(p.request.url);body=JSON.parse(p.request.postData)}catch{continue}
        if(u.origin==='https://wjk.jsrd.gov.cn:8004' && u.pathname==='/api/back/backDist/getSyPage' && body.title===q && body.searchType==='0' && body.pidLevel==='SY01' && !body.fullText && !body.deptID && !body.timeLines && !body.documentNO && !body.issueYear && !body.path && !body.issueDateStartDate && !body.issueDateEndDate && !body.implementDate && !body.impleEndDate && Array.isArray(body.theme) && body.theme.length===0)ids.add(p.requestId);
      }
      if(x.method==='Network.responseReceived' && p.response?.status===200 && p.response?.mimeType==='application/json')ok.add(p.requestId);
      if(x.method==='Network.loadingFinished')done.add(p.requestId);
    }
    const id=[...ids].find(x=>ok.has(x)&&done.has(x)); if(!id){await new Promise(r=>setTimeout(r,150));continue;}
    const response=await c.send('Network.getResponseBody',{requestId:id});if(response.base64Encoded||!response.body)throw Error('无法读取搜索响应');
    const d=JSON.parse(response.body);if(d.result?.code!==4000||!Array.isArray(d.result?.data))throw Error('搜索响应结构异常');
    const clean=s=>String(s||'').replace(/<[^>]*>/g,'').replace(/&amp;/g,'&').replace(/&lt;/g,'<').replace(/&gt;/g,'>').replace(/&quot;/g,'"').replace(/&#39;/g,"'").trim();
    const groups=d.result.data.map(x=>{validateJiangsuCategory(x);return {category:x.name,category_code:x.code,total:x.list.total,items:x.list.records.map(v=>({id:v.id,title:clean(v.title),agency:v.deptName,publication_date:v.issueDate,effective_date:v.implementDate,status_code:v.timeLines}))};});
    if(groups.some(x=>x.items.some(v=>!v.id||!v.title)))throw Error('搜索题录缺失');
    return {source:'江苏省法规规章规范性文件数据库，正常浏览器首页检索响应',query:q,groups,note:'各类别仅首页至多 10 条；总数是分类总数。结果含现行、修改和废止版本，状态码须依据站方核对；正文与后续效力尚未通过接口验证。'};
  }
  throw Error('未捕获与关键词匹配的江苏法规库搜索响应');
}
