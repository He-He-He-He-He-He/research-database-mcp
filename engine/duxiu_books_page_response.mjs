import {parseDuxiuBooksDocument} from './duxiu_books_response.mjs';

/** 读取读秀学校会话中正常翻页得到的图书题录 HTML。 */
export async function duxiuBooksPage(tab,query,pageNumber,submitPage){
 if(typeof query!=='string'||!query.trim()||query.length>100||!Number.isInteger(pageNumber)||pageNumber<2||pageNumber>1000||typeof submitPage!=='function')throw Error('需提供检索词、页码和正常翻页回调');
 const q=query.trim(),before=await tab.playwright.evaluate(()=>({host:location.hostname,path:location.pathname,search:location.search,body:document.body.innerText}));
 let u=new URLSearchParams(before.search);if(before.host!=='book.duxiu.com'||before.path!=='/search'||u.get('sw')!==q||u.get('Field')!=='all'||!before.body.includes('浙江大学'))throw Error('机构或全部字段查询不符');
 let c=await tab.capabilities.get('cdp');await c.send('Network.enable');let methods=['Network.requestWillBeSent','Network.responseReceived','Network.loadingFinished','Network.loadingFailed'];let cursor=(await c.readEvents({methods})).cursor;
 await submitPage();let ids=new Set(),ok=new Set(),done=new Set(),failed=new Set();
 for(let deadline=Date.now()+25000;Date.now()<deadline;){let ev=await c.readEvents({afterSequence:cursor,methods,timeoutMs:1000,limit:1000});cursor=ev.cursor;if(ev.truncated)throw Error('网络事件不完整');
  for(let e of ev.events){let p=e.params||{};
   if(e.method==='Network.requestWillBeSent'&&p.request?.method==='GET'&&p.type==='Document')try{let x=new URL(p.request.url);if(x.origin==='https://book.duxiu.com'&&x.pathname==='/search'&&x.searchParams.get('sw')===q&&x.searchParams.get('Field')==='all'&&Number(x.searchParams.get('Pages'))===pageNumber)ids.add(p.requestId)}catch{}
   if(e.method==='Network.responseReceived'&&p.response?.status===200&&(p.response?.mimeType||'').includes('text/html'))ok.add(p.requestId);if(e.method==='Network.loadingFinished')done.add(p.requestId);if(e.method==='Network.loadingFailed')failed.add(p.requestId);
  }
  let id=[...ids].find(x=>ok.has(x)&&done.has(x));if(!id){if([...ids].some(x=>failed.has(x)))throw Error('读秀分页请求失败');await new Promise(r=>setTimeout(r,200));continue}
  let raw=await c.send('Network.getResponseBody',{requestId:id});let html=raw.base64Encoded?Buffer.from(raw.body,'base64').toString('utf8'):raw.body;let parsed=parseDuxiuBooksDocument(html);
  let screen;for(let i=0;i<30;i++){screen=await tab.playwright.evaluate(()=>({host:location.hostname,path:location.pathname,search:location.search,body:document.body?.innerText||'',ids:[...document.querySelectorAll('dt.books-title a[href]')].map(a=>{try{return new URL(a.href).searchParams.get('dxNumber')}catch{return null}}).filter(Boolean)}));if(parsed.items.every(x=>screen.ids.includes(x.id))&&screen.body.includes('浙江大学'))break;await new Promise(r=>setTimeout(r,200));}
  let p=new URLSearchParams(screen.search);if(screen.host!=='book.duxiu.com'||screen.path!=='/search'||p.get('sw')!==q||p.get('Field')!=='all'||Number(p.get('Pages'))!==pageNumber||!screen.body.includes('浙江大学')||parsed.items.some(x=>!screen.ids.includes(x.id)))throw Error('机构、页码或页面题录不符');
  return {source:'读秀浙江大学图书检索',query:q,page:pageNumber,total:parsed.total,items:parsed.items,note:'全部字段普通检索正常分页，最多15条标题；未验证单本馆藏、阅读或全文权限。'};
 }
 throw Error('未捕获相符的读秀分页响应');
}
