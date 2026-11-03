import {validateCadalResponseCounts} from './cadal_response_counts.mjs';
/** CADAL 墓志碑帖的真实首屏搜索响应。 */
export async function cadalInscriptionsResponse(tab, query, submitSearch) {
 if(typeof query!=='string'||!query.trim()||query.length>100||query.includes('^^')||typeof submitSearch!=='function') throw Error('需要有效关键词和站内检索回调');
 const q=query.trim(), c=await tab.capabilities.get('cdp'); await c.send('Network.enable');
 const methods=['Network.requestWillBeSent','Network.responseReceived','Network.loadingFinished']; let cur=(await c.readEvents({methods})).cursor; await submitSearch();
 const ids=new Set(),ok=new Set(),done=new Set();
 for(let deadline=Date.now()+25000;Date.now()<deadline;){
  const e=await c.readEvents({afterSequence:cur,methods,limit:1000,timeoutMs:1000});cur=e.cursor;if(e.truncated)throw Error('网络事件不完整');
  for(const x of e.events){const p=x.params||{}; if(x.method==='Network.requestWillBeSent'&&p.request?.url==='https://tecang.cadal.edu.cn/metadata/api/tsk/port/v1.0/searchAll'&&p.request.method==='POST') {let f;try{f=JSON.parse(p.request.postData)}catch{continue} if(f.dbname==='inscriptions'&&f.collectionSearchType==='onecollectionsearch'&&f.curpage===1&&f.pagesize===30&&JSON.stringify(f.sfields)===JSON.stringify([`all^^${q}^^wildcard`])&&JSON.stringify(f.sortWord)===JSON.stringify(['hitcount:1'])&&!f.filter&&!f.filters)ids.add(p.requestId)} if(x.method==='Network.responseReceived'&&p.response?.status===200&&p.response?.mimeType==='application/json')ok.add(p.requestId);if(x.method==='Network.loadingFinished')done.add(p.requestId)}
  const id=[...ids].find(v=>ok.has(v)&&done.has(v));if(!id){await new Promise(r=>setTimeout(r,200));continue}
  const b=await c.send('Network.getResponseBody',{requestId:id});if(b.base64Encoded||!b.body)throw Error('无法读取站方响应');const d=JSON.parse(b.body);validateCadalResponseCounts(d);
  const page=await tab.playwright.evaluate(()=>({host:location.hostname,path:location.pathname,keyword:new URL(location.href).searchParams.get('keyword')}));if(page.host!=='tecang.cadal.edu.cn'||page.path!=='/collection/list/tV_dlN7_LPk='||page.keyword!==`all^^${q}^^wildcard`)throw Error('页面馆藏或检索词不符');
  const field=(list,key)=>list?.find(x=>x.key===key)?.value?.fieldvalue??null;
  const items=d.data.dataTablemaps.map(v=>({id:field(v.notDisplayed,'docid'),database:field(v.notDisplayed,'dbname'),collection:field(v.notDisplayed,'dbtitle'),title:typeof field(v.custom,'title')==='string'?field(v.custom,'title').replace(/<\/?span\b[^>]*>/g,''):null,creator:typeof field(v.custom,'creator')==='string'?field(v.custom,'creator').replace(/<\/?span\b[^>]*>/g,''):null,dynasty:field(v.custom,'date_dynasty'),period:field(v.custom,'date_chineasetime')}));
  if(items.some(v=>v.id===null||!v.title)||items.length>30)throw Error('题录缺少必要字段');return {source:'CADAL 墓志碑帖',query:q,page:1,total:d.data.total,items,note:'站方搜索响应的首屏书目；当前页面未确认机构登录、原件影像权限或其他分页；CADAL 禁止爬虫批量下载，自动题录转交助手的许可尚未确认。'};
 }throw Error('未捕获墓志碑帖检索响应');
}
