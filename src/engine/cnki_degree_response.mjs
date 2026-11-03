/** 捕获用户发起的知网学位论文检索响应；只读首屏题录。 */
export async function cnkiDegreeSearchResponse(tab,query,degree,submitSearch){
 if(typeof query!=='string'||!query.trim()||query.length>200||!['博士','硕士'].includes(degree)||typeof submitSearch!=='function')throw Error('需要关键词、博士或硕士范围以及提交搜索的回调');
 const q=query.trim(), c=await tab.capabilities.get('cdp');await c.send('Network.enable');let cur=(await c.readEvents({methods:['Network.responseReceived','Network.loadingFinished','Network.loadingFailed']})).cursor;
 await submitSearch();let requestId=null,finished=new Set(),failed=new Set();
 for(let i=0;i<16&&!(requestId&&finished.has(requestId));i++){
  const ev=await c.readEvents({afterSequence:cur,methods:['Network.responseReceived','Network.loadingFinished','Network.loadingFailed'],timeoutMs:3000,limit:1000});cur=ev.cursor;if(ev.truncated)throw Error('网络事件不完整');
  for(const e of ev.events){const p=e.params||{};if(e.method==='Network.responseReceived'&&p.response?.url?.split('?')[0]==='https://kns.cnki.net/kns8s/brief/grid'&&p.response.status===200&&p.response.mimeType==='text/html')requestId=p.requestId; if(e.method==='Network.loadingFinished')finished.add(p.requestId);if(e.method==='Network.loadingFailed')failed.add(p.requestId);}
  if(requestId&&failed.has(requestId))throw Error('题录请求失败');
 }
 if(!requestId||!finished.has(requestId))throw Error('未收到完整题录响应');const raw=await c.send('Network.getResponseBody',{requestId});if(raw.base64Encoded||typeof raw.body!=='string')throw Error('无法读取题录响应');
 for(let i=0;i<10;i++){
  const d=await tab.playwright.evaluate(()=>({q:document.querySelector('#txt_search')?.value?.trim(),body:document.body.innerText,institution:document.querySelector('[title="浙江大学图书馆"]')?.getAttribute('title')||null,items:[...document.querySelectorAll('table.result-table-list tbody tr')].filter(x=>x.getClientRects().length).map(x=>{const a=x.querySelector('td.name a');return {title:a?.innerText.trim(),url:a?.href,author:x.querySelector('td.author')?.innerText.trim()||null,school:x.querySelector('td.unit')?.innerText.trim()||null,year:x.querySelector('td.date')?.innerText.trim()||null}}).filter(x=>x.title&&x.url)}));
  const esc=q.replace(/[.*+?^${}()|[\]\\]/g,'\\$&');const range=new RegExp('检索范围[：:]\\s*'+degree+'\\s+主题[：:]\\s*'+esc);const total=d.body.match(/共找到\s*([\d,]+)\s*条结果\s*1\//);
  if(d.q===q&&range.test(d.body)&&d.institution&&total&&d.items.length&&d.items.every(x=>{const v=new URL(x.url).searchParams.get('v');return v&&raw.body.includes(v)}))return {source:'中国知网学位论文',degree,query:q,institution:d.institution,total:Number(total[1].replaceAll(',','')),items:d.items,note:'首屏题录；实际 HTML 响应与页面文献标识核对，未验证全文。'};
 }
 throw Error('响应、检索条件或页面结果尚未一致；请检查页面');
}
