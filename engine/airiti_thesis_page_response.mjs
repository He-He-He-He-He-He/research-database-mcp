/** 华艺浙大会话中，正常翻页的学位论文题录响应。 */
export async function airitiThesisPage(tab,query,pageNumber,submitPage){
 if(typeof query!=='string'||!query.trim()||query.length>100||!Number.isInteger(pageNumber)||pageNumber<2||pageNumber>1000||typeof submitPage!=='function')throw Error('需提供检索词、页码和正常翻页回调');
 const q=query.trim();
 let before=await tab.playwright.evaluate(()=>({host:location.hostname,path:location.pathname,query:new URLSearchParams(location.search).get('sc[0].sk'),body:document.body.innerText,types:[...document.querySelectorAll('.col_academicPresent')].map(x=>x.innerText.includes('学位论文'))}));
 if(before.host!=='www.airitilibrary.cn'||before.path!=='/Article/Query'||before.query!==q||!before.body.includes('浙江大学')||!before.types.length||before.types.some(x=>!x))throw Error('当前机构、关键词或记录类型不符');
 let c=await tab.capabilities.get('cdp');await c.send('Network.enable');let methods=['Network.requestWillBeSent','Network.responseReceived','Network.loadingFinished','Network.loadingFailed'];let cursor=(await c.readEvents({methods})).cursor;
 await submitPage();let ids=new Set(),ok=new Set(),done=new Set(),failed=new Set();
 for(let deadline=Date.now()+25000;Date.now()<deadline;){
  let ev=await c.readEvents({afterSequence:cursor,methods,limit:1000,timeoutMs:1000});cursor=ev.cursor;if(ev.truncated)throw Error('网络事件不完整');
  for(let e of ev.events){let p=e.params||{};
   if(e.method==='Network.requestWillBeSent'&&p.request?.method==='GET'&&p.type==='Document')try{let u=new URL(p.request.url);if(u.origin==='https://www.airitilibrary.cn'&&u.pathname==='/Article/Query'&&u.searchParams.get('sc[0].sk')===q&&Number(u.searchParams.get('p'))===pageNumber&&Number(u.searchParams.get('ps'))===10)ids.add(p.requestId)}catch{}
   if(e.method==='Network.responseReceived'&&p.response?.status===200&&(p.response?.mimeType||'').includes('text/html'))ok.add(p.requestId);
   if(e.method==='Network.loadingFinished')done.add(p.requestId);if(e.method==='Network.loadingFailed')failed.add(p.requestId);
  }
  let id=[...ids].find(x=>ok.has(x)&&done.has(x));if(!id){if([...ids].some(x=>failed.has(x)))throw Error('论文分页请求失败');await new Promise(r=>setTimeout(r,200));continue}
  let b=await c.send('Network.getResponseBody',{requestId:id});if(b.base64Encoded||typeof b.body!=='string')throw Error('无法读取论文响应');
  let parts=b.body.split('<div class="col_academicPresent">').slice(1);if(!b.body.includes('浙江大学')||!parts.length||parts.length>10||parts.some(p=>!/<span>学位论文<\/span>/.test(p)))throw Error('机构或论文类型不符');
  let clean=s=>s?.replace(/<[^>]*>/g,'').replace(/&amp;/g,'&').replace(/&lt;/g,'<').replace(/&gt;/g,'>').replace(/&quot;/g,'"').replace(/&#39;/g,"'").trim()||null;
  let items=parts.map(p=>({id:p.match(/class="Result_選擇" key="([^"]+)"/)?.[1],title:clean(p.match(/<h3 class="ustyle_heading_H3">[\s\S]*?<a [^>]*>([\s\S]*?)<\/a>/)?.[1]),authors:clean(p.match(/<span class="author">([\s\S]*?)<\/span>\s*<\/div>/)?.[1]),source:clean(p.match(/<span class="source"[^>]*>([\s\S]*?)<\/span>/)?.[1]),type:'学位论文'}));
  let screen;for(let i=0;i<30;i++){screen=await tab.playwright.evaluate(()=>({host:location.hostname,path:location.pathname,search:location.search,body:document.body?.innerText||'',types:[...document.querySelectorAll('.col_academicPresent')].map(x=>x.innerText.includes('学位论文')),ids:[...document.querySelectorAll('.col_academicPresent .Result_選擇')].map(x=>x.getAttribute('key'))}));if(screen.ids.length)break;await new Promise(r=>setTimeout(r,200));}let u=new URLSearchParams(screen.search);
  if(screen.host!=='www.airitilibrary.cn'||screen.path!=='/Article/Query'||u.get('sc[0].sk')!==q||Number(u.get('p'))!==pageNumber||!screen.body.includes('浙江大学')||screen.types.some(x=>!x)||items.some(x=>!x.id||!x.title||!screen.ids.includes(x.id)))throw Error('机构、页码、分类或网页记录不符');
  return {source:'华艺学位论文学校会话',query:q,page:pageNumber,items,note:'每条均验证学位论文标记；不返回摘要或全文，学校订阅范围与单篇权限以原站为准。'};
 }
 throw Error('未捕获论文分页响应');
}
