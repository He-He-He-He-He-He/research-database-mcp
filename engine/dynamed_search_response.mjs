/** Capture bounded topic metadata from a real DynaMed search response. */
export async function dynamedSearchResponse(tab,query,submitSearch,limit=5){

 if(typeof query!=='string'||!query.trim()||query.length>100||(submitSearch!==undefined&&typeof submitSearch!=='function')||!Number.isInteger(limit)||limit<1||limit>10)throw Error('需要关键词、可选检索回调及1–10条上限');
 const q=query.trim(),c=await tab.capabilities.get('cdp');await c.send('Network.enable');let cur=(await c.readEvents({methods:['Network.responseReceived','Network.loadingFinished','Network.loadingFailed']})).cursor;
 if(submitSearch) await submitSearch(); else {await tab.playwright.locator('#autosuggest').fill(q); await tab.playwright.locator('#autosuggest').press('Enter');}
 let id=null,finished=new Set(),failed=new Set();
 for(let n=0;n<12&&!(id&&finished.has(id));n++){
  let ev=await c.readEvents({afterSequence:cur,methods:['Network.responseReceived','Network.loadingFinished','Network.loadingFailed'],timeoutMs:3000,limit:1000});cur=ev.cursor;if(ev.truncated)throw Error('网络事件不完整');
  for(const e of ev.events){let p=e.params||{};if(e.method==='Network.responseReceived'&&p.response?.url?.split('?')[0]==='https://www.dynamed.com/api/search/v3/results'&&p.response.status===200)id=p.requestId;if(e.method==='Network.loadingFinished')finished.add(p.requestId);if(e.method==='Network.loadingFailed')failed.add(p.requestId)}
  if(id&&failed.has(id))throw Error('检索请求失败');
 }
 if(!id||!finished.has(id))throw Error('未收到完整搜索响应');let raw=await c.send('Network.getResponseBody',{requestId:id});if(raw.base64Encoded||typeof raw.body!=='string')throw Error('无法读取响应');let v=JSON.parse(raw.body).viewModel;let u=new URL(await tab.url());
 if(u.hostname!=='www.dynamed.com'||u.pathname!=='/results'||u.searchParams.get('q')!==q||v?.header?.title!==q||!Array.isArray(v?.tabContents?.main?.primaryResults))throw Error('搜索条件或响应范围不匹配');
 let list=v.tabContents.main.primaryResults;return {source:'DynaMed',query:q,total:v.tabs?.find(x=>x.id==='main')?.count,items:list.slice(0,limit).map(x=>({id:x.id,type:x.header,title:x.contentLink?.label,url:x.contentLink?.route?.startsWith('/')?'https://www.dynamed.com'+x.contentLink.route:null})),note:'捕获一次普通搜索首屏主题题录；不包含临床正文，机构授权、全文、分页及第三方AI使用许可未验证。医学信息需由专业人员判断。'};
}
