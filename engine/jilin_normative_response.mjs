/** 捕获用户正常操作吉林行政规范性文件库的 JSONP 搜索响应。 */
export function validateJilinResults(d){if(d?.pageIndex!==1||d.pageSize!==15||!Number.isSafeInteger(d.totalCount)||d.totalCount<0||!Array.isArray(d.list)||d.list.length>15||d.list.length>d.totalCount)throw Error('原站分页或总数异常')}
export async function jilinNormativeResponse(tab, query, submitSearch) {
 if(typeof query!=='string'||!query.trim()||query.length>100||typeof submitSearch!=='function')throw Error('需要 1–100 字关键词和正常搜索回调');
 const q=query.trim(), c=await tab.capabilities.get('cdp');await c.send('Network.enable');
 const methods=['Network.requestWillBeSent','Network.responseReceived','Network.loadingFinished'];let cursor=(await c.readEvents({methods})).cursor;
 await submitSearch();const ids=new Set(),ok=new Set(),done=new Set();
 for(const end=Date.now()+20000;Date.now()<end;){
  const e=await c.readEvents({afterSequence:cursor,methods,limit:1000,timeoutMs:1000});cursor=e.cursor;if(e.truncated)throw Error('网络事件不完整');
  for(const x of e.events){const p=x.params||{};
   if(x.method==='Network.requestWillBeSent'&&p.request?.method==='GET'){
    let u,k;try{u=new URL(p.request.url);k=decodeURIComponent(u.searchParams.get('keyword')||'')}catch{continue}
    if(u.origin==='https://infogate.jl.gov.cn'&&u.pathname==='/govsearch/jsonp/gkml_xzgf20221026.jsp'&&k===q&&u.searchParams.get('keywordCategory')==='title'&&u.searchParams.get('channelid')===''&&u.searchParams.get('page')==='1'&&u.searchParams.get('size')==='15'&&u.searchParams.get('callback')==='result')ids.add(p.requestId);
   }
   if(x.method==='Network.responseReceived'&&p.response?.status===200)ok.add(p.requestId);
   if(x.method==='Network.loadingFinished')done.add(p.requestId);
  }
  const id=[...ids].find(i=>ok.has(i)&&done.has(i));if(!id){await new Promise(r=>setTimeout(r,100));continue}
  const b=await c.send('Network.getResponseBody',{requestId:id});if(b.base64Encoded||!b.body)throw Error('无法读取搜索响应');
  const m=b.body.match(/^\s*result\((\{[\s\S]*\})\);?\s*$/);if(!m)throw Error('原站 JSONP 结构异常');const d=JSON.parse(m[1]);
  validateJilinResults(d);
  return {source:'吉林省行政规范性文件库，浏览器响应',query:q,total:d.totalCount,page:1,items:d.list,note:'全部部门标题检索首屏；效力、正文和其他分页须核对原站。'};
 }
 throw Error('未捕获与关键词对应的吉林规范性文件搜索响应');
}
