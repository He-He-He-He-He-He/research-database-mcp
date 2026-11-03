/** Scopus 机构网页正常翻页的题录响应。调用者提供点击目标页的操作。 */
export function validateScopusPageData(data,offset){if(!Array.isArray(data?.items)||!Number.isSafeInteger(data.metadata?.totalCount)||data.metadata.totalCount<0||data.metadata.offset!==offset||data.metadata.itemCount!==10||data.items.length>10||data.items.length>Math.max(0,data.metadata.totalCount-offset))throw Error('分页响应结构或页码异常')}
export async function scopusPageResponse(tab, query, pageNumber, submitPage) {
 if (typeof query !== 'string' || !query.trim() || query.length > 150 || !Number.isInteger(pageNumber) || pageNumber < 2 || pageNumber > 200 || typeof submitPage !== 'function') throw Error('须提供关键词、2–200 页及正常翻页回调');
 const q=query.trim(), offset=(pageNumber-1)*10, c=await tab.capabilities.get('cdp');
 await c.send('Network.enable');
 const methods=['Network.requestWillBeSent','Network.responseReceived','Network.loadingFinished','Network.loadingFailed'];
 let cursor=(await c.readEvents({methods})).cursor;
 await submitPage();
 const ids=new Set(),ok=new Set(),done=new Set(),failed=new Set();
 for (let deadline=Date.now()+25000;Date.now()<deadline;) {
  const events=await c.readEvents({afterSequence:cursor,methods,timeoutMs:3000,limit:1000}); cursor=events.cursor;
  if(events.truncated) throw Error('网络事件不完整');
  for(const e of events.events) { const p=e.params||{};
   if(e.method==='Network.requestWillBeSent' && p.request?.url?.split('?')[0]==='https://www.scopus.com/gateway/documents/search' && p.request.method==='POST') {
    try {const b=JSON.parse(p.request.postData);if(b.query===`TITLE-ABS-KEY(${q})` && b.documentClassification==='primary' && b.resultSet?.offset===offset && b.resultSet?.itemCount===10) ids.add(p.requestId)}catch{}
   }
   if(e.method==='Network.responseReceived' && p.response?.status===200 && p.response?.mimeType==='application/json')ok.add(p.requestId);
   if(e.method==='Network.loadingFinished')done.add(p.requestId);
   if(e.method==='Network.loadingFailed')failed.add(p.requestId);
  }
  const id=[...ids].find(x=>ok.has(x)&&done.has(x));
  if(!id){if([...ids].some(x=>failed.has(x)))throw Error('Scopus 翻页请求失败');await new Promise(resolve=>setTimeout(resolve,200));continue}
  const r=await c.send('Network.getResponseBody',{requestId:id});if(r.base64Encoded || typeof r.body!=='string')throw Error('无法读取搜索响应');
  const data=JSON.parse(r.body);
  validateScopusPageData(data,offset);
  const items=data.items.map(x=>({id:x.scopusId||null,title:x.title||'',authors:(x.authors||[]).map(a=>a.preferredName?.full).filter(Boolean),source:x.source?.title||null,year:x.pubYear??null,doi:x.doi||null,citations:x.citations?.count??null,url:x.scopusId?`https://www.scopus.com/pages/publications/${encodeURIComponent(x.scopusId)}`:null}));
  if(items.some(x=>!x.id||!x.title))throw Error('响应题录缺少必要字段');
  let screen;for(let i=0;i<50;i++){screen=await tab.playwright.evaluate(()=>({host:location.hostname,body:document.body.innerText,values:[...document.querySelectorAll('input')].map(x=>x.value),ids:[...document.querySelectorAll('a[href*="/pages/publications/"]')].map(x=>x.getAttribute('href').split('?')[0].split('/').pop())}));
   if(screen.host==='www.scopus.com'&&screen.body.includes('Zhejiang University Library')&&screen.values.includes(q)&&items.every(x=>screen.ids.includes(x.id)))break;await new Promise(resolve=>setTimeout(resolve,200));}
  if(screen.host!=='www.scopus.com'||!screen.body.includes('Zhejiang University Library')||!screen.values.includes(q))throw Error('页面机构或检索词不一致');
  if(items.some(x=>!screen.ids.includes(x.id)))throw Error('响应题录与网页记录不一致');
  return {source:'Scopus 机构会话题录',query:q,page:pageNumber,total:data.metadata.totalCount,items,note:'网页正常翻页响应，每页 10 条；网页可浏览范围与上游总数可能不同；不含摘要及全文。'};
 }
 throw Error('未捕获相符的 Scopus 分页响应');
}
