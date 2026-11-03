/** Taylor & Francis eBooks：捕获浏览器会话实际搜索页 JSON。 */
export async function taylorBooksResponse(tab, query, submitSearch, page = 1) {
 if(typeof query!=='string'||!query.trim()||query.length>200||/[\x00-\x1f]/.test(query)||typeof submitSearch!=='function')throw Error('需要关键词与正常提交搜索的回调');
 if(!Number.isInteger(page)||page<1||page>5)throw Error('仅支持前 5 页');
 const q=query.trim(), c=await tab.capabilities.get('cdp');await c.send('Network.enable');
 const methods=['Network.requestWillBeSent','Network.responseReceived','Network.loadingFinished','Network.loadingFailed'];let cur=(await c.readEvents({methods})).cursor;
 await submitSearch(); const ids=new Set(),ok=new Set(),bad=new Set(),done=new Set(),failed=new Set(),deadline=Date.now()+20000;
 for(let i=0;i<40&&Date.now()<deadline;i++){
  const ev=await c.readEvents({afterSequence:cur,methods,timeoutMs:3000,limit:1000});cur=ev.cursor;if(ev.truncated)throw Error('网络事件不完整');
  if(!ev.events.length)await new Promise(resolve=>setTimeout(resolve,250));
  for(const e of ev.events){const p=e.params||{};
   if(e.method==='Network.requestWillBeSent'&&p.request?.url?.split('?')[0]==='https://api.taylorfrancis.com/v5/search/books'&&p.request.method==='POST')try{let b=JSON.parse(p.request.postData);if(b.keyword===q&&b.limit===10&&b.offset===(page-1)*10)ids.add(p.requestId)}catch{}
   if(e.method==='Network.responseReceived'&&p.response?.status===200&&p.response?.mimeType==='application/json')ok.add(p.requestId);
   else if(e.method==='Network.responseReceived')bad.add(p.requestId);
   if(e.method==='Network.loadingFinished')done.add(p.requestId);if(e.method==='Network.loadingFailed')failed.add(p.requestId);
  }
  let id=[...ids].find(x=>ok.has(x)&&done.has(x));if(!id){if([...ids].some(x=>failed.has(x)||bad.has(x)))throw Error('电子书搜索请求失败或非 JSON 响应');continue}
  let raw=await c.send('Network.getResponseBody',{requestId:id});if(raw.base64Encoded||typeof raw.body!=='string')throw Error('无法读取题录响应');let d=JSON.parse(raw.body);if(d.metadata?.status!=='Success'||!Array.isArray(d.data?.resultSet)||(!Number.isInteger(d.data.productCount)||d.data.productCount<0))throw Error('题录响应格式异常');
  if(d.data.resultSet.length>10||(d.data.productCount>(page-1)*10&&d.data.resultSet.length===0))throw Error('站方题录数量与请求不一致');
  let state=await tab.playwright.evaluate(()=>({url:location.href,query:document.querySelector('#searchTerm-header')?.value||'',body:document.body.innerText,current:document.querySelector('.ngx-pagination .current')?.innerText||''}));let u=new URL(state.url);
  if(u.hostname!=='www.taylorfrancis.com'||u.pathname!=='/search'||u.searchParams.get('key')!==q||state.query.trim()!==q||!/Search Results/.test(state.body)||((page>1||state.current)&&!new RegExp('(?:^|\\s)'+page+'$').test(state.current.trim())))throw Error('页面搜索词或页码与响应不一致');
  const clean=v=>typeof v==='string'&&!/[a-z][a-z0-9+.-]*:\/\/|www\.|(?:href|src)\s*=|(?:token|session|sid|apikey|api_key)\s*=/i.test(v)?v:null;
  let items=d.data.resultSet.map(x=>{let v=(x.identifiers?.urls||[]).find(y=>y.name==='ubx')?.url, url=null;try{let z=new URL(v,'https://www.taylorfrancis.com/');if(z.protocol==='https:'&&z.hostname==='www.taylorfrancis.com'&&!z.username&&!z.password&&z.pathname.startsWith('/books/'))url=z.origin+z.pathname}catch{};return {id:clean(x.id),title:clean(x.title),authors:(Array.isArray(x.contributors)?x.contributors:[]).map(a=>clean(a?.fullName||a?.name)).filter(Boolean),doi:clean(x.identifiers?.doi),isbn:clean(x.identifiers?.isbn),url,year:Number.isInteger(x.product?.copyright?.year)?x.product.copyright.year:null}}).filter(x=>x.title&&x.id);
  if(items.length!==d.data.resultSet.length)throw Error('题录项目缺少必要字段');
  return {source:'Taylor & Francis eBooks 页面书目',query:q,page,page_size:10,total:d.data.productCount,items,note:'当前页面筛选条件下的图书元数据；排序及分词由站方决定，版权年份不一定是出版日期。临时浏览器会话；未确认浙大机构身份及全文权限。链接只保留官方路径、不含查询参数。'};
 }throw Error('未捕获相符的电子书页 JSON 响应');
}

/** Open the ordinary search page and navigate the first five source pages. */
export async function searchTaylorBooks(tab, query, page = 1) {
 if(typeof query!=='string'||!query.trim()||query.length>200||/[\x00-\x1f]/.test(query))throw Error('关键词须为 1–200 字单行文本');
 if(!Number.isInteger(page)||page<1||page>5)throw Error('仅支持前 5 页');
 const q=query.trim();
 await tab.goto('https://www.taylorfrancis.com/search?key='+encodeURIComponent(q));
 return taylorBooksResponse(tab,q,async()=>{
  await tab.reload();
  if(page>1){
   await tab.playwright.locator('ul[aria-label="Pagination"] li.pagination-next a').waitFor({state:'visible',timeoutMs:20000});
   for(let n=2;n<=page;n++){
    await tab.playwright.locator('ul[aria-label="Pagination"] li.pagination-next a').click();
    await tab.playwright.locator('ul[aria-label="Pagination"] li.current').getByText(String(n),{exact:true}).waitFor({state:'visible',timeoutMs:20000});
   }
  }
 },page);
}
