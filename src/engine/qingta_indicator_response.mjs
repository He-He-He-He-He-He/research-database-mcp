/* 青塔全景云：在已登录页面捕获用户主动查询的单次响应。 */
export function parseQingtaMenu(body) {
 const j=JSON.parse(body);
 if(j.state!==0 || !Array.isArray(j.data?.list)) throw Error('青塔指标目录响应异常');
 return j.data.list.map(x=>({id:x.id,label:x.label,parentId:x.parentId,mainId:x.mainId,onlyDetail:x.onlyDetail}));
}
export function parseQingtaStatistics(body,id) {
 const j=JSON.parse(body),d=j.data;
 if(j.state!==0 || !d || String(d.indexid)!==String(id) || !Array.isArray(d.columnData) || !Array.isArray(d.tableData)) throw Error('青塔指标数据与所选指标不一致或响应异常');
 return {indexid:d.indexid,indexname:d.indexname,columnData:d.columnData,tableData:d.tableData,totalNum:d.totalNum,totalData:d.totalData,explain:d.explain};
}
async function capture(tab,path,match,action) {
 if(typeof action!=='function') throw Error('需要用户正常查询页面的操作回调');
 const c=await tab.capabilities.get('cdp'); await c.send('Network.enable');
 const methods=['Network.requestWillBeSent','Network.responseReceived','Network.loadingFinished'];let cursor=(await c.readEvents({methods})).cursor;
 await action(); const requests=new Set(),ok=new Set(),done=new Set();
 for(const end=Date.now()+20000;Date.now()<end;){
  const batch=await c.readEvents({afterSequence:cursor,methods,limit:1000,timeoutMs:1000});cursor=batch.cursor;if(batch.truncated)throw Error('青塔网络事件不完整');
  for(const e of batch.events){const p=e.params||{};
   if(e.method==='Network.requestWillBeSent'&&p.request?.method==='POST') {try {const u=new URL(p.request.url);if(u.origin==='https://ud.cingta.com'&&u.pathname===path&&match(JSON.parse(p.request.postData||'{}')))requests.add(p.requestId)}catch{}}
   if(e.method==='Network.responseReceived'&&p.response?.status===200)ok.add(p.requestId);
   if(e.method==='Network.loadingFinished')done.add(p.requestId);
  }
  const id=[...requests].find(x=>ok.has(x)&&done.has(x));if(!id)continue;
  const b=await c.send('Network.getResponseBody',{requestId:id});return b.base64Encoded?Buffer.from(b.body,'base64').toString('utf8'):b.body;
 }
 throw Error('未捕获青塔页面的对应查询响应，请检查登录和页面状态');
}
export async function qingtaMenu(tab,keyword,action){
 if(typeof keyword!=='string'||!keyword.trim()||keyword!==keyword.trim()||keyword.length>100)throw Error('需要不超过100字的搜索关键词');
 const body=await capture(tab,'/basedata/menus-query/',x=>x.keyword===keyword,action);
 const items= parseQingtaMenu(body);
 return {source:'青塔全景云',query:keyword,source_count:items.length,items:items.slice(0,50),truncated:items.length>50,note:'指标目录搜索，非统计数据或全文；仅返回前50项，需有效登录会话。'};
}
export async function qingtaStatistics(tab,id,action){
 if(!/^\d{1,10}$/.test(String(id)))throw Error('需要指标目录的数字 id');
 const body=await capture(tab,'/basedata/get_countdata/',x=>typeof x.EncryptParam==='string'&&x.EncryptParam.length>0,action);
 return {source:'青塔全景云',...parseQingtaStatistics(body,id),note:'单次页面统计结果；筛选条件、年份、单位、分页及附属机构口径以页面和响应为准；仅验证指标编号，不独立验证加密请求中的筛选条件。'};
}
