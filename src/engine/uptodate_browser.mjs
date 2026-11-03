/** Read only the title metadata from one ordinary institutional search response. */
export function parseUpToDate(body,query,visible,limit=3){
 if(typeof body!=='string'||body.length>8_000_000||typeof query!=='string'||!query.trim()||query.length>100||!Number.isInteger(limit)||limit<1||limit>10)throw Error('检索参数或响应异常');
 let x;try{x=JSON.parse(body)}catch{throw Error('响应不是 JSON')};let d=x?.data;
 if(d?.searchTerm?.toLowerCase()!==query.trim().toLowerCase()||!Array.isArray(d.searchResults)||!Number.isInteger(d.total)||visible?.institution!=='浙江大学'||visible?.query?.toLowerCase()!==query.trim().toLowerCase())throw Error('检索词或机构会话未确认');
 let rows=d.searchResults.filter(r=>!r.hideInResults && typeof r.url==='string').slice(0,limit).map(r=>({id:r.id,title:r.title,type:r.type,path:typeof r.url==='string'?r.url.split('?')[0]:null}));
 if(!rows.length||rows.some(r=>!/^\d+$/.test(r.id)||!r.title||!/^\/contents\//.test(r.path)||!visible.paths.includes(r.path)))throw Error('页面题录与响应未匹配');
 return {source:'UpToDate（浙江大学机构会话）',query:query.trim(),total:d.total,records:rows,note:'仅专题题录；本站明确限制自动化及 AI 处理内容，学校的额外授权尚未确认。非医疗建议。'};
}
export async function upToDateSearch(tab,query,submitSearch,limit=3){
 if(typeof submitSearch!=='function'||typeof query!=='string'||!query.trim()||query.length>100)throw Error('检索参数无效');
 const c=await tab.capabilities.get('cdp'), methods=['Network.responseReceived','Network.loadingFinished','Network.loadingFailed'];await c.send('Network.enable');let cursor=(await c.readEvents({methods})).cursor;await submitSearch();let id,done=false;const deadline=Date.now()+20000;
 while(Date.now()<deadline){let batch=await c.readEvents({methods,afterSequence:cursor,timeoutMs:1500,limit:500});cursor=batch.cursor;if(batch.truncated)throw Error('网络事件不完整');for(const e of batch.events){let p=e.params||{};if(e.method==='Network.responseReceived'&&p.response?.status===200){let u;try{u=new URL(p.response.url)}catch{}if(u?.hostname==='www.uptodate.cn'&&u.pathname==='/services/app/contents/search/2/json'&&u.searchParams.get('search')?.toLowerCase()===query.trim().toLowerCase())id=p.requestId}if(id&&p.requestId===id&&e.method==='Network.loadingFinished')done=true;if(id&&p.requestId===id&&e.method==='Network.loadingFailed')throw Error('检索响应失败')}
 if(done){let r=await c.send('Network.getResponseBody',{requestId:id});if(r.base64Encoded)throw Error('响应编码不支持');for(let i=0;i<30;i++){let v=await tab.playwright.evaluate(()=>({institution:document.querySelector('#wkUtdWelcomeName')?.innerText?.trim(),query:document.querySelector('#tbSearch')?.value,paths:[...document.querySelectorAll('a[href^="/contents/"]')].map(a=>a.getAttribute('href').split('?')[0])}));try{return parseUpToDate(r.body,query,v,limit)}catch(e){if(e.message!=='页面题录与响应未匹配')throw e}await new Promise(resolve=>setTimeout(resolve,250))}throw Error('页面题录未与响应同步')}
 await new Promise(resolve=>setTimeout(resolve,200));}throw Error('未收到本次检索响应');
}
