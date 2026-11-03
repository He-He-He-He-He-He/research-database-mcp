/** 从 CADAL 当前搜索页正常翻页，读取实际 HTML 响应中的题录标题。 */
export async function cadalSearchPage(tab,query,pageNumber,submitPage){
 if(typeof query!=='string'||!query.trim()||query.length>100||!Number.isInteger(pageNumber)||pageNumber<2||pageNumber>10000||typeof submitPage!=='function')throw Error('需提供检索词、页码及正常翻页回调');
 const q=query.trim(),c=await tab.capabilities.get('cdp');
 const before=await tab.playwright.evaluate(()=>({host:location.hostname,path:location.pathname,body:document.body.innerText}));
 if(before.host!=='cadal.edu.cn'||before.path!=='/cadalinfo/search'||!before.body.includes(q))throw Error('当前 CADAL 搜索词不符');
 await c.send('Network.enable'); const methods=['Network.requestWillBeSent','Network.responseReceived','Network.loadingFinished','Network.loadingFailed']; let cursor=(await c.readEvents({methods})).cursor;
 await submitPage(); const ids=new Set(),ok=new Set(),done=new Set(),failed=new Set();
 for(let deadline=Date.now()+25000;Date.now()<deadline;){
  let es=await c.readEvents({afterSequence:cursor,methods,timeoutMs:3000,limit:1000});cursor=es.cursor;if(es.truncated)throw Error('网络事件不完整');
  for(const e of es.events){let p=e.params||{};
   if(e.method==='Network.requestWillBeSent' && p.request?.method==='GET' && p.type==='Document')try{let u=new URL(p.request.url);if(u.origin==='https://cadal.edu.cn'&&u.pathname==='/cadalinfo/search'&&Number(u.searchParams.get('currentPage'))===pageNumber&&u.searchParams.get('searchId'))ids.add(p.requestId)}catch{}
   if(e.method==='Network.responseReceived'&&p.response?.status===200&&(p.response?.mimeType||'').includes('html'))ok.add(p.requestId);
   if(e.method==='Network.loadingFinished')done.add(p.requestId);if(e.method==='Network.loadingFailed')failed.add(p.requestId);
  }
  let id=[...ids].find(x=>ok.has(x)&&done.has(x));if(!id){if([...ids].some(x=>failed.has(x)))throw Error('分页请求失败');await new Promise(r=>setTimeout(r,200));continue}
  let raw=await c.send('Network.getResponseBody',{requestId:id});if(raw.base64Encoded||typeof raw.body!=='string')throw Error('无法读取 HTML 响应');
  let pattern=/<a\s+class="title"[^>]*onclick="bookCardPageGo\('([^']+)'[^\"]*"[^>]*>([\s\S]*?)<\/a>/g;
  let records=[...raw.body.matchAll(pattern)].map(m=>({id:m[1],title:m[2].replace(/<[^>]*>/g,'').replace(/\s+/g,' ').trim()}));
  if(!records.length||records.length>10||records.some(x=>!/^\d+$/.test(x.id)||!x.title))throw Error('响应题录未识别');
  let screen=await tab.playwright.evaluate(()=>({host:location.hostname,path:location.pathname,search:location.search,body:document.body.innerText,ids:[...document.querySelectorAll('a.title[onclick]')].map(a=>{let m=a.getAttribute('onclick').match(/bookCardPageGo\('([^']+)'/);return m&&m[1]}).filter(Boolean)}));
  let u=new URLSearchParams(screen.search);if(screen.host!=='cadal.edu.cn'||screen.path!=='/cadalinfo/search'||Number(u.get('currentPage'))!==pageNumber||!screen.body.includes(q)||records.some(x=>!screen.ids.includes(x.id)))throw Error('页码、检索词或记录与网页不符');
  return {source:'CADAL 原站浏览器搜索响应',query:q,page:pageNumber,items:records,note:'混合馆藏单页标题及编号；学校机构身份、影像和全文权限未验证。标题中的 HTML 实体保留原样。'};
 }
 throw Error('未捕获匹配分页响应');
}
