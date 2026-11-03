/** 龙源学校电子阅览室正常滚动加载的期刊目录响应。 */
export async function longyuanMagazinePage(tab,query,pageNumber,loadPage){
 if(typeof query!=='string'||!query.trim()||query.length>100||!Number.isInteger(pageNumber)||pageNumber<2||pageNumber>1000||typeof loadPage!=='function')throw Error('需要刊名词、续页页码和正常加载回调');
 let q=query.trim(),before=await tab.playwright.evaluate(()=>({host:location.hostname,body:document.body.innerText}));
 if(before.host!=='zju.dps.qikan.cn'||!before.body.includes('浙江大学电子阅览室')||!before.body.includes(q))throw Error('学校或刊名查询页不符');
 let c=await tab.capabilities.get('cdp');await c.send('Network.enable');let methods=['Network.requestWillBeSent','Network.responseReceived','Network.loadingFinished','Network.loadingFailed'];let cursor=(await c.readEvents({methods})).cursor;
 await loadPage();let ids=new Set(),ok=new Set(),done=new Set(),failed=new Set();
 for(let deadline=Date.now()+25000;Date.now()<deadline;){let ev=await c.readEvents({afterSequence:cursor,methods,timeoutMs:1000,limit:1000});cursor=ev.cursor;if(ev.truncated)throw Error('网络事件不完整');
  for(let e of ev.events){let p=e.params||{};
   if(e.method==='Network.requestWillBeSent'&&p.request?.method==='GET')try{let u=new URL(p.request.url);if(u.origin==='https://zju.dps.qikan.cn'&&u.pathname==='/api/magazine/search'&&u.searchParams.get('keyword')===q&&Number(u.searchParams.get('pageindex'))===pageNumber&&Number(u.searchParams.get('pagesize'))===18)ids.add(p.requestId)}catch{}
   if(e.method==='Network.responseReceived'&&p.response?.status===200&&(p.response?.mimeType||'').includes('json'))ok.add(p.requestId);if(e.method==='Network.loadingFinished')done.add(p.requestId);if(e.method==='Network.loadingFailed')failed.add(p.requestId);
  }
  let id=[...ids].find(x=>ok.has(x)&&done.has(x));if(!id){if([...ids].some(x=>failed.has(x)))throw Error('期刊加载失败');await new Promise(r=>setTimeout(r,200));continue}
  let b=await c.send('Network.getResponseBody',{requestId:id});if(b.base64Encoded||typeof b.body!=='string')throw Error('响应不可读取');let data=JSON.parse(b.body);
  if(data.Code!==1||data.PageIndex!==pageNumber||data.PageSize!==18||!Number.isInteger(data.ItemCount)||!Array.isArray(data.Data)||data.Data.length>18)throw Error('分页结构异常');
  let items=data.Data.map(x=>({id:x.ID,title:x.Name,year:x.Year??null,issue:x.Issue??null}));
  let screen;for(let i=0;i<30;i++){screen=await tab.playwright.evaluate(()=>({host:location.hostname,body:document.body?.innerText||'',titles:[...document.querySelectorAll('h5')].map(x=>x.innerText.trim())}));if(items.every(x=>screen.titles.includes(x.title)))break;await new Promise(r=>setTimeout(r,200));}
  if(screen.host!=='zju.dps.qikan.cn'||!screen.body.includes('浙江大学电子阅览室')||items.some(x=>!x.id||!x.title||!screen.titles.includes(x.title)))throw Error('响应与学校页面记录不一致');
  return {source:'龙源浙江大学电子阅览室',query:q,page:pageNumber,pages:data.PageTotal,total:data.ItemCount,items,note:'刊名检索的正常续页；期号为上游原值，不含文章全文、下载参数或逐刊阅读权限。'};
 }
 throw Error('未捕获期刊续页响应');
}
