/** 知网工具书词目检索：读取当前会话真实响应。 */
export async function cnkiReferenceResponse(tab, query, submitSearch) {
 if(typeof query!=='string'||!query.trim()||query.length>200||typeof submitSearch!=='function')throw Error('需要关键词和正常提交搜索的回调');const q=query.trim();
 const c=await tab.capabilities.get('cdp');await c.send('Network.enable');const methods=['Network.requestWillBeSent','Network.responseReceived','Network.loadingFinished','Network.loadingFailed'];let cur=(await c.readEvents({methods})).cursor;await submitSearch();const ids=new Set(),ok=new Set(),finished=new Set(),failed=new Set();
 for(let i=0;i<16;i++){
  const ev=await c.readEvents({afterSequence:cur,methods,timeoutMs:3000,limit:1000});cur=ev.cursor;if(ev.truncated)throw Error('网络事件不完整');
  for(const e of ev.events){const p=e.params||{};
   if(e.method==='Network.requestWillBeSent'&&p.request?.url?.split('?')[0]==='https://t.cnki.net/rbook-api/v1/criteria/query'&&p.request.method==='POST')try{const b=JSON.parse(p.request.postData),a=b.q?.userScope?.items||[];if(b.resource==='CROSSDB'&&b.product==='TOTAL'&&b.start===1&&b.size===20&&a.some(x=>x.uf==='ET'&&x.uv===q)&&a.some(x=>x.uf==='LC'&&x.uv==='Y'))ids.add(p.requestId)}catch{}
   if(e.method==='Network.responseReceived'&&p.response?.status===200&&p.response?.mimeType==='application/json')ok.add(p.requestId);if(e.method==='Network.loadingFinished')finished.add(p.requestId);if(e.method==='Network.loadingFailed')failed.add(p.requestId);
  }
  const id=[...ids].find(x=>ok.has(x)&&finished.has(x));if(!id){if([...ids].some(x=>failed.has(x)))throw Error('词目请求失败');continue}const raw=await c.send('Network.getResponseBody',{requestId:id});if(raw.base64Encoded||typeof raw.body!=='string')throw Error('无法读取词目响应');const data=JSON.parse(raw.body);if(data.code!==0||!Array.isArray(data.data?.data))throw Error('词目响应格式异常');
  for(let j=0;j<12;j++){
   await tab.getAXState({emit:false});const page=await tab.playwright.evaluate(()=>({q:document.querySelector('#inputK')?.value?.trim(),institution:document.querySelector('#Ecp_top_logout_showLayer1')?.innerText||'',body:document.body.innerText}));
   if(page.q===q&&page.institution.includes('浙江大学')&&/检索选项[：:]\s*词目/.test(page.body)){
    const items=data.data.data.map(row=>{const m=Object.fromEntries((row.metadata||[]).map(x=>[x.name,x.value]));return {id:m.FN||null,title:(m.TI||'').replace(/<[^>]*>/g,''),book:m.BTI||null,bookId:m.BID||null,words:m.NOC||null}}).filter(x=>x.id&&x.title);return {source:'CNKI 中国工具书网络出版总库',query:q,total:data.data.total,institution:page.institution,items,note:'精确词目首屏元数据；全文及订阅权限未验证。'};
   }
  }throw Error('页面未显示相符的词目范围或机构身份');
 }throw Error('未收到符合工具书精确词目条件的完整响应');
}
