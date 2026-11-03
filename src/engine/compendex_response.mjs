/** Engineering Village 单次检索实际 JSON 响应，仅 Compendex 首屏。 */
export async function compendexResponse(tab, query, submitSearch) {
 if(typeof query!=='string'||!query.trim()||query.length>150||typeof submitSearch!=='function')throw Error('需要关键词及页面正常提交检索的回调');
 const q=query.trim(),c=await tab.capabilities.get('cdp');await c.send('Network.enable');
 const methods=['Network.requestWillBeSent','Network.responseReceived','Network.loadingFinished','Network.loadingFailed'];let cur=(await c.readEvents({methods})).cursor;await submitSearch();
 const submitted=new Set(),redirected=new Set(),ok=new Set(),done=new Set();
 for(let deadline=Date.now()+30000;Date.now()<deadline;){
  const es=await c.readEvents({afterSequence:cur,methods,limit:1000,timeoutMs:1000});cur=es.cursor;if(es.truncated)throw Error('网络事件不完整');
  for(const e of es.events){let p=e.params||{},u=p.request?.url||'';
   if(e.method==='Network.requestWillBeSent'&&u.split('?')[0]==='https://www.engineeringvillage.com/search/submit.url'&&p.request.method==='POST'){
    let f=new URLSearchParams(p.request.postData||'');if(f.get('searchWord1')===q&&f.get('database')==='1'&&f.get('section1')==='NO-LIMIT')submitted.add(p.requestId);
   }
   if(e.method==='Network.requestWillBeSent'&&u.startsWith('https://www.engineeringvillage.com/search/results/quick.url?')&&new URL(u).searchParams.get('database')==='1'&&submitted.has(p.requestId))redirected.add(p.requestId);
   if(e.method==='Network.responseReceived'&&p.response?.url?.startsWith('https://www.engineeringvillage.com/search/results/quick.url?')&&p.response.status===200&&p.response.mimeType==='application/json')ok.add(p.requestId);
   if(e.method==='Network.loadingFinished')done.add(p.requestId);
  }
  const id=[...submitted].find(x=>redirected.has(x)&&ok.has(x)&&done.has(x));if(!id){await new Promise(r=>setTimeout(r,200));continue}
  let b=await c.send('Network.getResponseBody',{requestId:id});if(b.base64Encoded||!b.body)throw Error('无法读取 Compendex 响应');let data=JSON.parse(b.body),m=data.searchMetaData;
  if(m?.database!=='1'||m?.foundINDBs!=='Compendex'||(!Number.isSafeInteger(m?.resultscount)||m.resultscount<0)||!m?.displayquery?.toLowerCase().includes(q.toLowerCase())||!Array.isArray(data.results))throw Error('Compendex 响应与检索不匹配');
  let page=await tab.playwright.evaluate(()=>({url:location.href,q:document.querySelector('input[name="searchWord1"]')?.value}));if(new URL(page.url).hostname!=='www.engineeringvillage.com'||page.q!==q)throw Error('当前页面与检索不匹配');
  const clean=x=>typeof x==='string'?x.replace(/<[^>]*>/g,'').replace(/&amp;/g,'&').replace(/&lt;/g,'<').replace(/&gt;/g,'>').replace(/&quot;/g,'"').replace(/&#39;/g,"'").trim():null;
  let items=data.results.map((x,i)=>({position:i+1,id:x.doc?.docid||null,title:clean(x.titleNoHighlight||x.title)||null,authors:(x.authors||[]).map(a=>clean(a.name)).filter(Boolean),source:clean(x.source),year:x.yr??null,doi:x.doi||null,database:x.doc?.dbname||null,document_type:x.doctypedisplay||null}));
  if(items.some(x=>x.id&&!x.id.startsWith('cpx_')))throw Error('返回非 Compendex 记录');
  return {source:'Engineering Village Compendex 机构会话题录',query:q,total:m.resultscount,items,note:'单次 Compendex 首屏响应，空记录原样保留；全文与分页未验证。遵循平台条款，不用于批量抓取或训练。'};
 }throw Error('未捕获匹配的 Compendex 首屏响应');
}
