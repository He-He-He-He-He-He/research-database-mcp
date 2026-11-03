/** Compendex 查询：已有浙大机构结果页，前 3 页，不返回会话信息。 */
import {compendexResponse} from './compendex_response.mjs';
const methods=['Network.requestWillBeSent','Network.responseReceived','Network.loadingFinished','Network.loadingFailed'];
const safe=v=>typeof v==='string'&&!/[a-z][a-z0-9+.-]*:\/\/|www\.|(?:href|src)\s*=|(?:token|session|sid|apikey|api_key)\s*=/i.test(v)?v:null;
const clean=v=>typeof v==='string'?v.replace(/<[^>]*>/g,'').replace(/&amp;/g,'&').replace(/&lt;/g,'<').replace(/&gt;/g,'>').replace(/&quot;/g,'"').replace(/&#39;/g,"'").trim():null;
function item(x,index) {
 const id=x?.id??x?.doc?.docid??null;
 if(id!==null&&(typeof id!=='string'||!/^cpx_[A-Za-z0-9_-]+$/.test(id)))throw Error('非 Compendex 记录或编号异常');
 const authors=Array.isArray(x?.authors)?x.authors.map(a=>safe(clean(typeof a==='string'?a:a?.name))).filter(Boolean):[];
 const year=x?.year??x?.yr??null;
 return {position:index,id,title:safe(clean(x?.titleNoHighlight||x?.title)),authors,source:safe(clean(x?.source)),year:typeof year==='string'||typeof year==='number'?year:null,doi:safe(x?.doi),database:safe(x?.database??x?.doc?.dbname),document_type:safe(x?.document_type??x?.doctypedisplay)};
}
async function nextPage(tab,query,page,total) {
 const c=await tab.capabilities.get('cdp');await c.send('Network.enable');let cur=(await c.readEvents({methods})).cursor;
 await tab.playwright.locator('a#next-page-top').first().click();
 await tab.playwright.getByText(new RegExp('\\b'+page+' of [\\d,]+ pages')).first().waitFor({state:'visible',timeoutMs:20000});
 const ids=new Set(),ok=new Set(),bad=new Set(),done=new Set(),deadline=Date.now()+20000;
 for(let n=0;n<40&&Date.now()<deadline;n++) {
  let ev=await c.readEvents({afterSequence:cur,methods,limit:1000,timeoutMs:1000});cur=ev.cursor;if(ev.truncated)throw Error('网络事件不完整');
  if(!ev.events.length)await new Promise(r=>setTimeout(r,250));
  for(const e of ev.events){let p=e.params||{};
   if(e.method==='Network.requestWillBeSent'&&p.request?.method==='GET')try{let u=new URL(p.request.url);if(u.origin==='https://www.engineeringvillage.com'&&u.pathname==='/search/results/quick.url'&&u.searchParams.get('navigator')==='NEXT'&&u.searchParams.get('COUNT')===String((page-1)*25+1)&&u.searchParams.get('database')==='1')ids.add(p.requestId)}catch{}
   if(e.method==='Network.responseReceived'&&p.response?.status===200&&p.response?.mimeType==='application/json')ok.add(p.requestId);else if(e.method==='Network.responseReceived')bad.add(p.requestId);
   if(e.method==='Network.loadingFinished')done.add(p.requestId);if(e.method==='Network.loadingFailed')bad.add(p.requestId);
  }
  let id=[...ids].find(x=>ok.has(x)&&done.has(x));if(!id){if([...ids].some(x=>bad.has(x)))throw Error('Compendex 翻页请求失败');continue}
  let r=await c.send('Network.getResponseBody',{requestId:id});if(r.base64Encoded||typeof r.body!=='string')throw Error('无法读取 Compendex 响应');
  let d=JSON.parse(r.body),m=d.searchMetaData;
  if(m?.database!=='1'||m?.foundINDBs!=='Compendex'||m?.resultscount!==total||!m?.displayquery?.toLowerCase().includes(query.toLowerCase())||!Array.isArray(d.results)||d.results.length>25)throw Error('Compendex 翻页结果与查询不一致');
  let state=await tab.playwright.evaluate(()=>({host:location.hostname,q:document.querySelector('input[name="searchWord1"]')?.value,body:document.body.innerText}));
  if(state.host!=='www.engineeringvillage.com'||state.q!==query||!new RegExp('\\b'+page+' of [\\d,]+ pages').test(state.body))throw Error('Compendex 页面查询或页码不一致');
  let items=d.results.map((x,i)=>{let expected=(page-1)*25+i+1;if(x?.doc?.hitindex!=null&&Number(x.doc.hitindex)!==expected)throw Error('来源记录序号与页码不符');return item(x,expected)});
  return items;
 }
 throw Error('未捕获匹配的 Compendex 翻页响应');
}
export async function searchCompendex(tab,query,page=1) {
 if(typeof query!=='string'||!query.trim()||query.length>150||/[\x00-\x1f]/.test(query))throw Error('关键词须为1–150字单行文本');
 if(!Number.isInteger(page)||page<1||page>3)throw Error('目前仅支持前3页');
 const q=query.trim();let state=await tab.playwright.evaluate(()=>({host:location.hostname,path:location.pathname,hasInput:!!document.querySelector('input[name="searchWord1"]')}));
 if(state.host!=='www.engineeringvillage.com'||!state.path.startsWith('/search/')||!state.hasInput)throw Error('请先在 Engineering Village 打开有效的 Compendex 结果页');
 let button=tab.playwright.getByRole('button',{name:'Institution',exact:true}),expanded=await button.getAttribute('aria-expanded');
 if(expanded!=='true')await button.click();
 try{if(!await tab.playwright.getByText('Zhejiang University Library',{exact:true}).isVisible())throw Error('未确认浙江大学机构会话');}finally{if(expanded!=='true')await button.click();}
 const first=await compendexResponse(tab,q,async()=>{
  await tab.playwright.getByRole('combobox',{name:'Input search terms field 1'}).fill(q);
  await tab.playwright.getByRole('form',{name:'Quick search form'}).getByRole('button',{name:'Search',exact:true}).click();
 });
 let items=first.items.map((x,i)=>item(x,i+1));
 if(page>1&&first.total<=(page-1)*25)throw Error('请求页超出站方返回的总页数');
 for(let n=2;n<=page;n++)items=await nextPage(tab,q,n,first.total);
 return {source:'Engineering Village Compendex 浙大机构会话题录',query:q,page,page_size:25,total:first.total,items,note:'已有有效结果页会话中正常检索并顺序翻页；仅返回题录，初始馆方入口可能停留表单。站方排序和结果数可能变化；不返回会话链接或凭据，全文权限未验证。'};
}
