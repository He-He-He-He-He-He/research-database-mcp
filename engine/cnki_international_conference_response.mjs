/** 已认证知网国际会议检索：观察真实请求和完整题录响应。 */
export async function cnkiInternationalConferenceResponse(tab,query,submitSearch){
 if(typeof query!=='string'||!query.trim()||query.length>200||typeof submitSearch!=='function')throw Error('需要关键词和正常提交搜索的回调');const q=query.trim();
 const c=await tab.capabilities.get('cdp');await c.send('Network.enable');const methods=['Network.requestWillBeSent','Network.responseReceived','Network.loadingFinished','Network.loadingFailed'];let cur=(await c.readEvents({methods})).cursor;await submitSearch();
 let ids=new Set(),finished=new Set(),failed=new Set(),ok=new Set();
 for(let i=0;i<16;i++){
  const ev=await c.readEvents({afterSequence:cur,methods,timeoutMs:3000,limit:1000});cur=ev.cursor;if(ev.truncated)throw Error('网络事件不完整');
  for(const e of ev.events){const p=e.params||{};
   if(e.method==='Network.requestWillBeSent'&&p.request?.url?.split('?')[0]==='https://kns.cnki.net/kns8s/brief/grid'&&p.request.method==='POST'){
    try{const params=new URLSearchParams(p.request.postData),body=JSON.parse(params.get('QueryJson'));const items=body.QNode?.QGroup?.flatMap(g=>g.Items||[])||[];if(body.Resource==='CONFERENCE'&&body.Rlang==='Chinese'&&body.Classid==='BPBAFJ5S'&&params.get('pageNum')==='1'&&items.some(x=>x.Field==='SU'&&x.Value===q))ids.add(p.requestId);}catch{}
   }
   if(e.method==='Network.responseReceived'&&p.response?.status===200&&p.response?.mimeType==='text/html')ok.add(p.requestId);
   if(e.method==='Network.loadingFinished')finished.add(p.requestId);if(e.method==='Network.loadingFailed')failed.add(p.requestId);
  }
  const id=[...ids].find(x=>ok.has(x)&&finished.has(x));if(!id){if([...ids].some(x=>failed.has(x)))throw Error('题录请求失败');continue;}
  const raw=await c.send('Network.getResponseBody',{requestId:id});if(raw.base64Encoded||typeof raw.body!=='string')throw Error('无法读取题录响应');
  for(let t=0;t<10;t++){
   const d=await tab.playwright.evaluate(()=>({q:document.querySelector('#txt_search')?.value?.trim(),body:document.body.innerText,institution:document.querySelector('[title="浙江大学图书馆"]')?.getAttribute('title')||null,items:[...document.querySelectorAll('table.result-table-list tbody tr')].filter(x=>x.getClientRects().length).map(x=>{let a=x.querySelector('td.name a');return {title:a?.innerText.trim(),url:a?.href,author:x.querySelector('td.author')?.innerText.trim()||null,conference:x.querySelector('td.hy-name')?.innerText.trim()||null,date:x.querySelector('td.date')?.innerText.trim()||null}}).filter(x=>x.title&&x.url)}));
   const escaped=q.replace(/[.*+?^${}()|[\]\\]/g,'\\$&');const scope=new RegExp('检索范围[：:]\\s*国际会议\\s+主题[：:]\\s*'+escaped);const count=d.body.match(/共找到\s*([\d,]+)\s*条结果\s*1\//);
   if(d.q===q&&scope.test(d.body)&&d.institution&&count&&d.items.length&&d.items.every(x=>{const v=new URL(x.url).searchParams.get('v');return v&&raw.body.includes(v)}))return {source:'CNKI 国际会议论文',query:q,total:Number(count[1].replaceAll(',','')),institution:d.institution,items:d.items,note:'国际会议首屏题录；不代表全文已获授权。'};
  }throw Error('响应与页面未一致');
 }
 throw Error('未收到符合国际会议条件的完整响应');
}
