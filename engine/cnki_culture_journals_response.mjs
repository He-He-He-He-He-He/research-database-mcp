/** 知网精品文化期刊：观察已授权浏览器会话中的检索响应。 */
export async function cnkiCultureJournalsResponse(tab, query, submitSearch) {
 if (typeof query !== 'string' || !query.trim() || query.length > 200 || typeof submitSearch !== 'function') throw Error('需要关键词和正常提交搜索的回调');
 const q=query.trim(), c=await tab.capabilities.get('cdp'); await c.send('Network.enable');
 const methods=['Network.requestWillBeSent','Network.responseReceived','Network.loadingFinished','Network.loadingFailed'];let cur=(await c.readEvents({methods})).cursor;
 await submitSearch();const ids=new Set(),ok=new Set(),finished=new Set(),failed=new Set();
 for(let i=0;i<16;i++) {
  const ev=await c.readEvents({afterSequence:cur,methods,timeoutMs:3000,limit:1000});cur=ev.cursor;if(ev.truncated)throw Error('网络事件不完整');
  for(const e of ev.events){const p=e.params||{};
   if(e.method==='Network.requestWillBeSent'&&p.request?.url?.split('?')[0]==='https://wenhua.cnki.net/urtpweb/search/data'&&p.request.method==='POST'){
    try{const b=JSON.parse(p.request.postData);const terms=b.searchQuery?.flatMap(g=>g.item||[])||[];if(b.sysId==='19'&&b.tableId==='131'&&b.start===0&&b.length===20&&terms.some(x=>x.key==='title'&&x.value===q))ids.add(p.requestId)}catch{}
   }
   if(e.method==='Network.responseReceived'&&p.response?.status===200&&p.response?.mimeType==='text/html')ok.add(p.requestId);
   if(e.method==='Network.loadingFinished')finished.add(p.requestId);if(e.method==='Network.loadingFailed')failed.add(p.requestId);
  }
  const id=[...ids].find(x=>ok.has(x)&&finished.has(x));if(!id){if([...ids].some(x=>failed.has(x)))throw Error('题录请求失败');continue}
  const raw=await c.send('Network.getResponseBody',{requestId:id});if(raw.base64Encoded||typeof raw.body!=='string')throw Error('无法读取题录响应');
  for(let t=0;t<10;t++){
   const d=await tab.playwright.evaluate(()=>({q:document.querySelector('input.urtp_search_value')?.value?.trim(),institution:document.querySelector('#Ecp_top_logout_showLayer1')?.innerText||'',body:document.body.innerText,items:[...document.querySelectorAll('table.layui-table tbody tr')].map(r=>{let td=r.querySelectorAll('td'),a=td[1]?.querySelector('a');return {title:a?.innerText.trim(),url:a?.href,author:td[2]?.innerText.trim()||null,publication:td[3]?.innerText.trim()||null,issue:td[4]?.innerText.trim()||null}}).filter(x=>x.title&&x.url)}));
   const count=d.body.match(/共找到\s*([\d,]+)\s*条，当前\s*1\s*\//);
   if(d.q===q&&d.institution.includes('浙江大学')&&count&&d.items.length&&d.items.every(x=>{let f=new URL(x.url).searchParams.get('filename');return f&&raw.body.includes(f)}))return {source:'CNKI 中国精品文化期刊文献库',query:q,total:Number(count[1].replaceAll(',','')),institution:d.institution,items:d.items,note:'精品文化期刊篇名首屏题录；不代表全文已获授权。'};
  }throw Error('响应与页面未一致');
 }
 throw Error('未收到符合精品文化期刊条件的完整响应');
}
