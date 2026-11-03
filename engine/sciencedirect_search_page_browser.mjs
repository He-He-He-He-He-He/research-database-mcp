/** 捕获 ScienceDirect 学校会话下用户正常翻页的题录响应。 */
export async function scienceDirectSearchPage(tab, query, pageNumber, submitPage){
 if(typeof query!=='string'||!query.trim()||query.length>150||!Number.isInteger(pageNumber)||pageNumber<2||pageNumber>100||typeof submitPage!=='function')throw Error('需提供检索词、2–100 页和网页翻页回调');
 const q=query.trim(),offset=(pageNumber-1)*25,c=await tab.capabilities.get('cdp');await c.send('Network.enable');
 const methods=['Network.requestWillBeSent','Network.responseReceived','Network.loadingFinished','Network.loadingFailed'];let cursor=(await c.readEvents({methods})).cursor;
 await submitPage();const ids=new Set(),ok=new Set(),done=new Set(),failed=new Set();
 for(let deadline=Date.now()+25000;Date.now()<deadline;){
  let events=await c.readEvents({afterSequence:cursor,methods,timeoutMs:3000,limit:1000});cursor=events.cursor;if(events.truncated)throw Error('网络事件不完整');
  for(let e of events.events){let p=e.params||{};
   if(e.method==='Network.requestWillBeSent' && p.request?.method==='GET')try{let u=new URL(p.request.url);if(u.origin==='https://www.sciencedirect.com'&&u.pathname==='/search/api'&&u.searchParams.get('qs')===q&&Number(u.searchParams.get('offset'))===offset)ids.add(p.requestId)}catch{}
   if(e.method==='Network.responseReceived'&&p.response?.status===200&&(p.response?.mimeType||'').includes('json'))ok.add(p.requestId);
   if(e.method==='Network.loadingFinished')done.add(p.requestId);if(e.method==='Network.loadingFailed')failed.add(p.requestId);
  }
  let id=[...ids].find(x=>ok.has(x)&&done.has(x));if(!id){if([...ids].some(x=>failed.has(x)))throw Error('分页请求失败');await new Promise(r=>setTimeout(r,200));continue}
  let raw=await c.send('Network.getResponseBody',{requestId:id});if(raw.base64Encoded||typeof raw.body!=='string')throw Error('响应无法读取');let data=JSON.parse(raw.body);
  if(!Array.isArray(data.searchResults)||!Number.isInteger(data.resultsFound)||data.searchResults.length>25)throw Error('响应格式异常');
  let screen=await tab.playwright.evaluate(()=>({host:location.hostname,path:location.pathname,search:location.search,body:document.body.innerText,ids:[...document.querySelectorAll('a[id^="title-"]')].map(a=>a.id.slice(6))}));
  let u=new URLSearchParams(screen.search);if(screen.host!=='www.sciencedirect.com'||screen.path!=='/search'||u.get('qs')!==q||Number(u.get('offset'))!==offset||!(/Zhejiang University Library|浙江大学图书馆/.test(screen.body)))throw Error('机构、检索词或页码不符');
  const plain=x=>typeof x==='string'?x.replace(/<[^>]*>/g,''):null;
  let items=data.searchResults.map(x=>({id:x.pii,title:plain(x.title),title_raw:x.title,authors:(x.authors||[]).map(y=>y.name).filter(Boolean),source:plain(x.sourceTitle),date:x.publicationDateDisplay||null,doi:x.doi||null,url:x.pii?'https://www.sciencedirect.com/science/article/pii/'+encodeURIComponent(x.pii):null}));
  if(items.some(x=>!x.id||!x.title||!screen.ids.includes(x.id)))throw Error('响应与页面题录不符');
  return {source:'ScienceDirect 浙大会话题录',query:q,page:pageNumber,results_found_raw:data.resultsFound,terminated_early:data.details?.terminatedEarly??null,timed_out:data.details?.timedOut??null,items,note:'页面正常翻页，单页最多25条；原站可能截断结果或仅显示最近年份，结果数须结合页面提示，非全文或逐篇访问权限。'};
 }
 throw Error('未捕获相符的分页响应');
}
