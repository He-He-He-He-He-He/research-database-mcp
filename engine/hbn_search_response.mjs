/** Capture a single HBN indicator search response in the active authorized browser session. */
export function validateHbnResults(res){const d=res?.data;if(res?.code!==0||!Array.isArray(d?.results)||d.pageNo!==0||!Number.isSafeInteger(d.total)||d.total<0||d.results.length>d.total)throw Error('响应结构、总数或分页不匹配')}
export async function hbnSearchResponse(tab,keyword,submitSearch,limit=5){
 if(typeof keyword!=='string'||!keyword.trim()||keyword.length>100||typeof submitSearch!=='function'||!Number.isInteger(limit)||limit<1||limit>10)throw Error('需要关键词、单次搜索回调和1–10条上限');
 const query=keyword.trim(),c=await tab.capabilities.get('cdp');await c.send('Network.enable');let cur=(await c.readEvents({methods:['Network.requestWillBeSent','Network.responseReceived','Network.loadingFinished','Network.loadingFailed']})).cursor;
 await submitSearch();let id=null,done=new Set(),failed=new Set(),statuses=new Map();
 for(let n=0;n<15&&!(id&&done.has(id));n++){
  let events=await c.readEvents({afterSequence:cur,methods:['Network.requestWillBeSent','Network.responseReceived','Network.loadingFinished','Network.loadingFailed'],timeoutMs:3000,limit:1000});cur=events.cursor;if(events.truncated)throw Error('网络事件不完整');
  for(const e of events.events){let p=e.params||{};
   if(e.method==='Network.requestWillBeSent'&&p.request?.method==='POST'&&p.request.url?.split('?')[0]==='https://data.harborn.cn/db/searchDb/esAllInfo'){
    let v;try{v=JSON.parse(p.request.postData||'{}')}catch{};if(v?.name===query&&String(v?.type)==='0'&&v?.dbId===''&&v?.pageNo===0)id=p.requestId;
   }
   if(e.method==='Network.responseReceived')statuses.set(p.requestId,p.response?.status);
   if(e.method==='Network.loadingFinished')done.add(p.requestId);if(e.method==='Network.loadingFailed')failed.add(p.requestId);
  }
  if(id&&failed.has(id))throw Error('搜索请求失败');
 }
 if(!id||!done.has(id))throw Error('未收到匹配查询的完整搜索响应；请确认默认全部搜索和第一页');
 if(statuses.get(id)!==200)throw Error('搜索响应不是 HTTP 200');
 let raw=await c.send('Network.getResponseBody',{requestId:id});if(raw.base64Encoded||typeof raw.body!=='string')throw Error('无法读取搜索响应');let res=JSON.parse(raw.body);
 validateHbnResults(res);
 let state=await tab.playwright.evaluate(()=>({host:location.hostname,path:location.pathname,query:new URL(location.href).searchParams.get('name'),institution:document.body?.innerText.includes('浙江大学')}));
 if(state.host!=='data.harborn.cn'||state.path!=='/search/index'||state.query!==query||!state.institution)throw Error('页面关键词或浙大会话不匹配');
 return {source:'HBN环球财经系列数据库',institution:'浙江大学（页面显示）',query,total:res.data.total,items:res.data.results.slice(0,limit).map(x=>({id:x.id,title:x.cn_name,english_title:x.en_name||null,code:x.code,unit:x.unit,database_id:x.dbid,path:[x.tree1name,x.tree2name,x.tree3name,x.tree4name,x.tree5name,x.tree6name].filter(Boolean),updated:x.update_time})),note:'学校会话单次默认跨库搜索首屏指标题录；不含指标数值，匹配数非独立来源数量，馆藏与具体指标权限、数据原始来源及第三方AI使用许可需分别核实。'};
}
