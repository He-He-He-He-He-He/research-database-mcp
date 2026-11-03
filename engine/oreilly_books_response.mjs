/** O'Reilly 单次用户操作的书籍筛选真实响应，仅读取题录首屏。 */
export async function oreillyBooksResponse(tab,query,submitSearch){
 if(typeof query!=='string'||!query.trim()||query.length>150||typeof submitSearch!=='function')throw Error('需要当前搜索词及书籍筛选回调');
 const q=query.trim(),c=await tab.capabilities.get('cdp');await c.send('Network.enable');const methods=['Network.requestWillBeSent','Network.responseReceived','Network.loadingFinished'];let cur=(await c.readEvents({methods})).cursor;await submitSearch();
 let ids=new Set(),ok=new Set(),done=new Set();
 for(let deadline=Date.now()+25000;Date.now()<deadline;){let e=await c.readEvents({afterSequence:cur,methods,limit:1000,timeoutMs:1000});cur=e.cursor;if(e.truncated)throw Error('网络事件不完整');
 for(let x of e.events){let p=x.params||{};if(x.method==='Network.requestWillBeSent'&&p.request?.method==='GET'){let u;try{u=new URL(p.request.url)}catch{continue}if(u.origin==='https://learning.oreilly.com'&&u.pathname==='/search/api/search/'&&u.searchParams.get('q')===q&&u.searchParams.get('type')==='book'&&u.searchParams.get('rows')==='50'&&!u.searchParams.has('start'))ids.add(p.requestId)}
 if(x.method==='Network.responseReceived'&&p.response?.status===200&&p.response?.mimeType==='application/json')ok.add(p.requestId);if(x.method==='Network.loadingFinished')done.add(p.requestId)}
 let id=[...ids].find(x=>ok.has(x)&&done.has(x));if(!id){await new Promise(r=>setTimeout(r,200));continue}let b=await c.send('Network.getResponseBody',{requestId:id});if(b.base64Encoded||!b.body)throw Error('无法读取响应');let d=JSON.parse(b.body).data;
 if(!Number.isInteger(d?.total)||d.start!==0||!Array.isArray(d.products)||d.products.some(x=>x.type!=='book'))throw Error('书籍响应格式不符');
 let page=await tab.playwright.evaluate(()=>({url:location.href,q:document.querySelector('#searchBar')?.value}));if(new URL(page.url).hostname!=='learning.oreilly.com'||page.q!==q)throw Error('页面关键词不匹配');
 return {source:'O\'Reilly 学校会话书籍题录',query:q,total:d.total,items:d.products.map(x=>({id:x.product_id,title:x.title,authors:x.authors||[],url:x.url,publishers:x.custom_attributes?.publishers||[],publication_date:x.custom_attributes?.publication_date||null})),note:'用户操作书籍筛选所得首屏，全文、分页与个别资源权限未验证。'};
 }throw Error('未捕获匹配的 O\'Reilly 书籍响应');
}
