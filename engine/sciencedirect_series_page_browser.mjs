/** 观察 ScienceDirect 学校订阅及赠阅书系目录的正常页面请求。 */
export function validateScienceDirectSeries(data,page){if(!data?.results||typeof data.results!=='object'||Array.isArray(data.results)||!Number.isSafeInteger(data.totalResults)||data.totalResults<0||!Number.isSafeInteger(data.noOfPages)||data.noOfPages<0||page>data.noOfPages)throw Error('目录响应结构异常');const rows=Object.values(data.results).flat();if(rows.length>data.totalResults||rows.some(x=>x?.contentTypeCode!=='BS'||typeof x.displayName!=='string'||!/^\/bookseries\/[a-z0-9-]+$/i.test(x.sdUrl||'')))throw Error('目录书系字段或数量异常');return rows}
export async function scienceDirectSeriesPage(tab, pageNumber, submitPage) {
 if(!Number.isInteger(pageNumber)||pageNumber<1||pageNumber>1000||typeof submitPage!=='function') throw Error('需提供页码和网页正常操作回调');
 const c=await tab.capabilities.get('cdp'); await c.send('Network.enable');
 const methods=['Network.requestWillBeSent','Network.responseReceived','Network.loadingFinished','Network.loadingFailed'];
 let cursor=(await c.readEvents({methods})).cursor; await submitPage();
 const ids=new Set(),ok=new Set(),done=new Set(),failed=new Set();
 for(let deadline=Date.now()+25000;Date.now()<deadline;) {
  const ev=await c.readEvents({afterSequence:cursor,methods,timeoutMs:3000,limit:1000});cursor=ev.cursor;
  if(ev.truncated)throw Error('网络事件不完整');
  for(const e of ev.events){let p=e.params||{};
   if(e.method==='Network.requestWillBeSent' && p.request?.method==='GET') {
    try {let u=new URL(p.request.url); if(u.origin==='https://www.sciencedirect.com' && u.pathname==='/browse/publications' && u.searchParams.get('contentType')==='BS' && u.searchParams.get('accessType')==='subscribed' && Number(u.searchParams.get('page')||1)===pageNumber)ids.add(p.requestId)}catch{}
   }
   if(e.method==='Network.responseReceived' && p.response?.status===200 && (p.response?.mimeType||'').includes('json'))ok.add(p.requestId);
   if(e.method==='Network.loadingFinished')done.add(p.requestId);
   if(e.method==='Network.loadingFailed')failed.add(p.requestId);
  }
  let id=[...ids].find(x=>ok.has(x)&&done.has(x));
  if(!id){if([...ids].some(x=>failed.has(x)))throw Error('目录请求失败');await new Promise(resolve=>setTimeout(resolve,200));continue}
  let raw=await c.send('Network.getResponseBody',{requestId:id});if(raw.base64Encoded||typeof raw.body!=='string')throw Error('无法读取目录响应');
  let data=JSON.parse(raw.body);let rows=validateScienceDirectSeries(data,pageNumber);
  let screen=await tab.playwright.evaluate(()=>({host:location.hostname,path:location.pathname,search:location.search,body:document.body.innerText,urls:[...document.querySelectorAll('a[href*="/bookseries/"]')].map(a=>a.getAttribute('href').split('?')[0])}));
  let u=new URLSearchParams(screen.search);if(screen.host!=='www.sciencedirect.com'||screen.path!=='/browse/journals-and-books'||u.get('contentType')!=='BS'||u.get('accessType')!=='subscribed'||Number(u.get('page')||1)!==pageNumber||!(/Zhejiang University Library|浙江大学图书馆/.test(screen.body)))throw Error('学校身份、筛选或页码不符');
  if(rows.some(x=>!screen.urls.some(u=>u.endsWith(x.sdUrl))))throw Error('响应和页面书系不一致');
  return {source:'ScienceDirect 浙大会话期刊和图书目录',scope:'网页筛选 Subscribed & complimentary 的书系',page:pageNumber,pages:data.noOfPages,total:data.totalResults,items:rows.map(x=>({title:x.displayName,url:'https://www.sciencedirect.com'+x.sdUrl})),note:'学校订阅与赠阅混合标记，不代表每卷或每章全文可读；不含章节正文。'};
 }
 throw Error('未捕获相符的书系目录响应');
}
