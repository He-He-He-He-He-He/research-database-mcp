/** Capture one normal 东方杂志总目 search and cross-check its visible issue tree. */
export function parseDongfangCatalog(body, rows, query) {
 if(typeof query!=='string'||!query.trim()||query.length>80||typeof body!=='string'||body.length>500000||!Array.isArray(rows)) throw Error('检索参数或响应异常');
 let data;try{data=JSON.parse(body)}catch{throw Error('目录响应不是 JSON')}
 if(!data||!Array.isArray(data.ids)||data.ids.some(x=>typeof x!=='string'||!/^c\d+$/.test(x))||new Set(data.ids).size!==data.ids.length)throw Error('目录响应编号异常');
 const byId=new Map();for(const row of rows){if(!row||!/^c\d+$/.test(row.id)||typeof row.date!=='string'||!row.date||!Array.isArray(row.sections)||row.sections.some(s=>typeof s!=='string'))throw Error('页面目录格式异常');byId.set(row.id,row)}
 if(byId.size!==data.ids.length||data.ids.some(id=>!byId.has(id)))throw Error('页面目录与响应不一致');
 return {source:'书同文《东方杂志》总目 via 浙江大学机构会话',query:query.trim(),issue_count:data.ids.length,issues:rows,note:'仅为关键词命中的期次及目录栏目，并非文章全文或全部文章标题；无匹配词的文章栏目不会显示。显示顺序以页面为准。'};
}
export async function dongfangCatalogResponse(tab,query,submitSearch){
 if(typeof query!=='string'||!query.trim()||query.length>80||typeof submitSearch!=='function')throw Error('检索参数无效');
 const c=await tab.capabilities.get('cdp'),methods=['Network.responseReceived','Network.loadingFinished','Network.loadingFailed'];await c.send('Network.enable');let cursor=(await c.readEvents({methods})).cursor;await submitSearch();let id=null,done=false;const deadline=Date.now()+20000;
 while(Date.now()<deadline){const e=await c.readEvents({methods,afterSequence:cursor,timeoutMs:2000,limit:1000});cursor=e.cursor;if(e.truncated)throw Error('网络事件不完整');for(const event of e.events){let p=event.params||{};if(event.method==='Network.responseReceived'&&p.response?.status===200){let u;try{u=new URL(p.response.url)}catch{};if(u?.hostname==='gujiku.unihan.com.cn'&&u.pathname==='/minguofy/api/oldcatalog/search/MinGuoFY/'+encodeURIComponent(query.trim()))id=p.requestId}if(id&&p.requestId===id&&event.method==='Network.loadingFinished')done=true;if(id&&p.requestId===id&&event.method==='Network.loadingFailed')throw Error('目录检索请求失败')}
 if(done){const u=new URL(await tab.url());if(u.hostname!=='gujiku.unihan.com.cn'||u.pathname!=='/MinGuoFY')throw Error('页面不是东方杂志总目');const body=await c.send('Network.getResponseBody',{requestId:id});if(body.base64Encoded)throw Error('目录响应编码异常');for(let i=0;i<20;i++){const state=await tab.playwright.evaluate(()=>({q:document.querySelector('input[ng-model="searchData"]')?.value,rows:[...document.querySelectorAll('li[id^="c"][aria-level="1"]:not(.jstree-hidden)')].map(e=>({id:e.id,date:e.querySelector(':scope > a')?.textContent.trim(),sections:[...e.querySelectorAll(':scope > ul > li:not(.jstree-hidden) > a')].map(a=>a.textContent.trim())}))}));if(state.q===query.trim()){try{return parseDongfangCatalog(body.body,state.rows,query)}catch(e){if(e.message!=='页面目录与响应不一致')throw e}}await new Promise(r=>setTimeout(r,250))}throw Error('页面目录未与响应同步')}
 await new Promise(r=>setTimeout(r,200));}throw Error('未收到目录检索响应');
}
