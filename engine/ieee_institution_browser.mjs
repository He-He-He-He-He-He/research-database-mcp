/** One normal IEEE Xplore search in a Zhejiang University session; title metadata only. */
export function parseIeeeInstitution(body,query,state,limit=3){
 if(typeof body!=='string'||body.length>10_000_000||typeof query!=='string'||!query.trim()||query.length>100||!Number.isInteger(limit)||limit<1||limit>10)throw Error('检索参数或响应异常');
 let d;try{d=JSON.parse(body)}catch{throw Error('响应不是 JSON')};const q=query.trim();
 if(d?.userInfo?.institutionName!=='Zhejiang University'||!Array.isArray(d.breadCrumbs)||!d.breadCrumbs.some(b=>b.children?.some(c=>c.value===q))||!Array.isArray(d.records)||!Number.isInteger(d.totalRecords)||state?.query!==q||state?.institution!=='Zhejiang University')throw Error('机构或搜索条件未确认');
 let records=d.records.slice(0,limit).map(r=>({id:r.articleNumber,title:r.articleTitle,doi:r.doi||null,year:r.publicationYear,publication:r.publicationTitle,type:r.contentType,path:r.documentLink,access_type:r.accessType}));
 if(!records.length||records.some(r=>!/^\d+$/.test(r.id)||!r.title||!/^\/document\/\d+\/?$/.test(r.path)||!state.ids.includes(r.id)))throw Error('页面记录与响应不一致');
 return {source:'IEEE Xplore（浙江大学机构会话）',query:q,total:d.totalRecords,records,note:'首屏题录；默认搜索全部结果，不代表逐条订阅或全文权限。本站保留文本数据挖掘及 AI 等权利。'};
}
export async function ieeeInstitutionSearch(tab,query,submitSearch,limit=3){
 if(typeof submitSearch!=='function'||typeof query!=='string'||!query.trim()||query.length>100)throw Error('检索参数无效');
 let c=await tab.capabilities.get('cdp'),methods=['Network.responseReceived','Network.loadingFinished','Network.loadingFailed'];await c.send('Network.enable');let cursor=(await c.readEvents({methods})).cursor;await submitSearch();let id,done=false;const deadline=Date.now()+20000;
 while(Date.now()<deadline){let b=await c.readEvents({methods,afterSequence:cursor,timeoutMs:1500,limit:500});cursor=b.cursor;if(b.truncated)throw Error('网络事件不完整');for(const e of b.events){const p=e.params||{};if(e.method==='Network.responseReceived'&&p.response?.status===200){let u;try{u=new URL(p.response.url)}catch{}if(u?.hostname==='ieeexplore.ieee.org'&&u.pathname==='/rest/search')id=p.requestId}if(id&&p.requestId===id&&e.method==='Network.loadingFinished')done=true;if(id&&p.requestId===id&&e.method==='Network.loadingFailed')throw Error('搜索请求失败')}
 if(done){const raw=await c.send('Network.getResponseBody',{requestId:id});if(raw.base64Encoded)throw Error('响应编码不支持');for(let i=0;i<30;i++){let s=await tab.playwright.evaluate(()=>({query:new URLSearchParams(location.search).get('queryText'),institution:document.body.innerText.includes('Zhejiang University')?'Zhejiang University':document.body.innerText.includes('浙江大学')?'Zhejiang University':'',ids:[...document.querySelectorAll('a[href*="/document/"]')].map(a=>(a.getAttribute('href').match(/^\/document\/(\d+)/)||[])[1]).filter(Boolean)}));try{return parseIeeeInstitution(raw.body,query,s,limit)}catch(err){if(err.message!=='页面记录与响应不一致')throw err}await new Promise(r=>setTimeout(r,250))}throw Error('页面结果未与响应同步')}
 await new Promise(r=>setTimeout(r,200));}throw Error('未收到本次搜索响应');
}
