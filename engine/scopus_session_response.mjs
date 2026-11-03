import {validateScopusPageData} from './scopus_page_response.mjs';
/** Scopus 单次用户触发检索首屏题录，仅捕获已授权浏览器会话真实响应。 */
export async function scopusSessionResponse(tab, query, submitSearch) {
 if(typeof query!=='string'||!query.trim()||query.length>150||typeof submitSearch!=='function')throw Error('需要关键词和正常提交检索的回调');
 const q=query.trim(),c=await tab.capabilities.get('cdp');await c.send('Network.enable');const methods=['Network.requestWillBeSent','Network.responseReceived','Network.loadingFinished','Network.loadingFailed'];let cur=(await c.readEvents({methods})).cursor;
 await submitSearch();const ids=new Set(),ok=new Set(),done=new Set(),failed=new Set();
 for(let deadline=Date.now()+25000;Date.now()<deadline;){
  let ev=await c.readEvents({afterSequence:cur,methods,timeoutMs:3000,limit:1000});cur=ev.cursor;if(ev.truncated)throw Error('网络事件不完整');
  for(const e of ev.events){const p=e.params||{};
   if(e.method==='Network.requestWillBeSent'&&p.request?.url?.split('?')[0]==='https://www.scopus.com/gateway/documents/search'&&p.request.method==='POST')try{let b=JSON.parse(p.request.postData);if(b.query===`TITLE-ABS-KEY(${q})`&&b.documentClassification==='primary'&&b.resultSet?.offset===0&&b.resultSet?.itemCount===10)ids.add(p.requestId)}catch{}
   if(e.method==='Network.responseReceived'&&p.response?.status===200&&p.response?.mimeType==='application/json')ok.add(p.requestId);
   if(e.method==='Network.loadingFinished')done.add(p.requestId);if(e.method==='Network.loadingFailed')failed.add(p.requestId);
  }
  let id=[...ids].find(x=>ok.has(x)&&done.has(x));if(!id){if([...ids].some(x=>failed.has(x)))throw Error('Scopus 请求失败');await new Promise(resolve=>setTimeout(resolve,200));continue}
  let r=await c.send('Network.getResponseBody',{requestId:id});if(r.base64Encoded||typeof r.body!=='string')throw Error('无法读取 Scopus 响应');let data=JSON.parse(r.body);
  validateScopusPageData(data,0);
  let page=await tab.playwright.evaluate(()=>({url:location.href,body:document.body.innerText,values:[...document.querySelectorAll('input')].map(x=>x.value)}));
  if(new URL(page.url).hostname!=='www.scopus.com'||!page.body.includes('Zhejiang University Library')||!page.values.includes(q))throw Error('页面机构或检索词与响应不一致');
  let items=data.items.map(x=>({id:x.scopusId||null,title:x.title||'',authors:(x.authors||[]).map(a=>a.preferredName?.full).filter(Boolean),source:x.source?.title||null,year:x.pubYear??null,doi:x.doi||null,citations:x.citations?.count??null,url:x.scopusId?`https://www.scopus.com/pages/publications/${encodeURIComponent(x.scopusId)}`:null})).filter(x=>x.id&&x.title);
  if(items.length!==data.items.length)throw Error('题录缺少必要字段');
  return {source:'Scopus 机构会话题录',query:q,total:data.metadata.totalCount,items,note:'标题、摘要、关键词字段的单次检索首屏；逐篇全文及分页未验证。遵循平台条款，不用于批量抓取或训练。'};
 }throw Error('未捕获相符的 Scopus 首屏响应');
}
