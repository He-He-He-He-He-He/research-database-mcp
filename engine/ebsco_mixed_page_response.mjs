/** EBSCO 浙大会话当前数据库集合的正常翻页响应。 */
export async function ebscoMixedPage(tab,query,pageNumber,submitPage){
 if(typeof query!=='string'||!query.trim()||query.length>100||!Number.isInteger(pageNumber)||pageNumber<2||pageNumber>1000||typeof submitPage!=='function')throw Error('需提供检索词、页码和网页翻页回调');
 const q=query.trim(),offset=(pageNumber-1)*10;
 let before=await tab.playwright.evaluate(()=>({host:location.hostname,q:document.querySelector('#search-input')?.value||'',body:document.body.innerText}));
 if(before.host!=='research.ebsco.com'||before.q.trim()!==q||!before.body.includes('ZHEJIANG UNIV'))throw Error('学校或检索词不符');
 let c=await tab.capabilities.get('cdp');await c.send('Network.enable');let methods=['Network.requestWillBeSent','Network.responseReceived','Network.loadingFinished','Network.loadingFailed'];let cursor=(await c.readEvents({methods})).cursor;
 await submitPage();let requests=new Map(),ok=new Set(),done=new Set(),failed=new Set();
 for(let deadline=Date.now()+25000;Date.now()<deadline;){let ev=await c.readEvents({afterSequence:cursor,methods,timeoutMs:1000,limit:1000});cursor=ev.cursor;if(ev.truncated)throw Error('网络事件不完整');
  for(let e of ev.events){let p=e.params||{};
   if(e.method==='Network.requestWillBeSent'&&p.request?.method==='POST'&&p.request.url?.split('?')[0]==='https://research.ebsco.com/api/search/v1/search')try{let b=JSON.parse(p.request.postData||'');let db=b.filters?.find(x=>x.id==='databases')?.values;if(b.query===q&&b.offset===offset&&b.count===10&&Array.isArray(db)&&db.length)requests.set(p.requestId,db)}catch{}
   if(e.method==='Network.responseReceived'&&p.response?.status===200&&(p.response?.mimeType||'').includes('json'))ok.add(p.requestId);if(e.method==='Network.loadingFinished')done.add(p.requestId);if(e.method==='Network.loadingFailed')failed.add(p.requestId);
  }
  let id=[...requests.keys()].find(x=>ok.has(x)&&done.has(x));if(!id){if([...requests.keys()].some(x=>failed.has(x)))throw Error('分页请求失败');await new Promise(r=>setTimeout(r,200));continue}
  let raw=await c.send('Network.getResponseBody',{requestId:id});if(raw.base64Encoded||typeof raw.body!=='string')throw Error('无法读取响应');let s=JSON.parse(raw.body).search;
  if(!s||s.query!==q||!Array.isArray(s.items)||s.items.length>10||!Number.isInteger(s.totalItems))throw Error('分页响应结构异常');
  let items=s.items.map(x=>({id:x.id,accession:x.an||null,database:x.longDbName||null,database_code:x.shortDbName||null,title_raw:x.title?.value||null,date:x.publicationDate||null,source:x.source||null,authors:(x.contributors||[]).map(z=>z.name).filter(Boolean),type:x.docTypeDisplayNames||[]}));
  let screen;for(let i=0;i<30;i++){screen=await tab.playwright.evaluate(()=>({host:location.hostname,q:document.querySelector('#search-input')?.value||'',body:document.body?.innerText||'',ids:[...document.querySelectorAll('a[href*="/search/details/"]')].map(x=>x.getAttribute('href').split('?')[0].split('/').pop())}));if(items.every(x=>screen.ids.includes(x.id)))break;await new Promise(r=>setTimeout(r,200));}
  if(screen.host!=='research.ebsco.com'||screen.q.trim()!==q||!screen.body.includes('ZHEJIANG UNIV')||items.some(x=>!x.id||!x.title_raw||!screen.ids.includes(x.id)))throw Error('学校、检索词或页面题录不符');
  return {source:'EBSCO 浙江大学机构会话',query:q,page:pageNumber,total:s.totalItems,selected_database_codes:requests.get(id),items,note:'当前所选数据库混合检索的正常续页；题名保留上游高亮标记，不返回摘要和全文；单篇访问权限另核。'};
 }
 throw Error('未捕获相符的 EBSCO 分页响应');
}
