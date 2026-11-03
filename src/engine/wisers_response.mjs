/** 慧科新闻搜索：捕获当前授权浏览器会话触发的题录响应。 */
export async function wisersResponse(tab, query, submitSearch) {
 if(typeof query!=='string'||!query.trim()||query.length>200||typeof submitSearch!=='function') throw Error('需要关键词及当前页面正常检索回调');
 const q=query.trim(), c=await tab.capabilities.get('cdp'); await c.send('Network.enable');
 const methods=['Network.requestWillBeSent','Network.responseReceived','Network.loadingFinished','Network.loadingFailed']; let cursor=(await c.readEvents({methods})).cursor;
 await submitSearch(); const ids=new Set(),ok=new Set(),done=new Set(),failed=new Set();
 for(let n=0;n<80;n++) {
  const events=await c.readEvents({afterSequence:cursor,methods,limit:1000,timeoutMs:3000}); cursor=events.cursor;
  if(events.truncated) throw Error('网络事件不完整，请重试');
  for(const e of events.events){ const p=e.params||{};
   if(e.method==='Network.requestWillBeSent'&&p.request?.url==='https://vertical-new-search.wisersone.com/wevo/api'&&p.request?.method==='POST') try {
    const req=JSON.parse(p.request.postData), g=req.requests?.g0, a=g?.params?.criteria;
    if(g?.params?.path==='search/searchresult'&&a?.keyword===q&&a?.startIdx===1&&a?.pageSize===50) ids.add(p.requestId);
   } catch {}
   if(e.method==='Network.responseReceived'&&p.response?.status===200&&p.response?.mimeType==='application/json')ok.add(p.requestId);
   if(e.method==='Network.loadingFinished')done.add(p.requestId); if(e.method==='Network.loadingFailed')failed.add(p.requestId);
  }
  const id=[...ids].find(x=>ok.has(x)&&done.has(x));
  if(!id){if([...ids].some(x=>failed.has(x)))throw Error('慧科检索请求失败'); await new Promise(resolve=>setTimeout(resolve,250)); continue}
  const raw=await c.send('Network.getResponseBody',{requestId:id});if(raw.base64Encoded||typeof raw.body!=='string')throw Error('无法读取慧科响应');
  const data=JSON.parse(raw.body)?.g0?.data;
  if(data?.path!=='getDocumentList'||data.code!=='50000'||!Array.isArray(data.data?.items)||!/^\d+$/.test(String(data.data.totalDocCount))) throw Error('慧科结果格式或状态不符合预期');
  const d=data.data;
  if(!d.progress?.finished)throw Error('慧科检索尚未结束');
  const items=d.items.map(x=>({id:x.docId||null,title:x.headline||null,source:x.source||null,published:x.publishDate||null,url:x.webUrl||null}));
  if(items.some(x=>!x.id||!x.title)) throw Error('慧科结果缺少题名或标识，请检查接口结构，未返回不完整的结果');
  const responseTotal=/^\d+$/.test(String(d.total))?Number(d.total):null;
  return {source:'WiseSearch 慧科新闻搜索',keyword:q,total:Number(d.totalDocCount),response_total:responseTotal,items,note:'当前会话的首屏题录；日期、媒体及排序沿用网页当前设置；正文、分页及具体订购权限未验证。'};
 }
 throw Error('未收到匹配关键词的完整慧科检索响应');
}
