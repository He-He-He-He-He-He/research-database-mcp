/** 已有浙大年鉴结果页上的普通检索及前2页，禁止输出来源链接参数。 */
import {cnkiYearbooksResponse} from './cnki_yearbooks_response.mjs';
const methods=['Network.requestWillBeSent','Network.responseReceived','Network.loadingFinished','Network.loadingFailed'];
const safe=v=>v==null?null:typeof v==='string'&&!/[a-z][a-z0-9+.-]*:\/\/|www\.|(?:href|src)\s*=|(?:token|session|sid|apikey|api_key)\s*=/i.test(v)?v:null;
function sanitize(x,index){let item={position:index},omitted=[];for(let k of ['title','publication','year','column']){item[k]=safe(x?.[k]);if(x?.[k]!=null&&item[k]===null)omitted.push(k)}if(omitted.length)item.source_fields_omitted=omitted;return item;}
async function indexOf(tab,id,kind){let s=await tab.getAXState({emit:false,disableDiffing:true});let m=s.match(new RegExp('^\\s*(\\d+)\\s+'+kind+'[^\\n]*ID: '+id+'\\b','m'));if(!m)throw Error('未找到所需页面控件');return Number(m[1]);}
async function nextPage(tab,q,page,total){
 let ready=false;for(let i=0;i<50;i++){let target=await tab.playwright.evaluate(()=>document.querySelector('#PageNext')?.getAttribute('data-curpage')||'');if(target===String(page)){ready=true;break}await new Promise(r=>setTimeout(r,200));}if(!ready)throw Error('知网下一页控件尚未更新');
 const c=await tab.capabilities.get('cdp');await c.send('Network.enable');let cur=(await c.readEvents({methods})).cursor;
 let index=await indexOf(tab,'PageNext','link');await tab.click(index);
 let ids=new Set(),ok=new Set(),done=new Set(),bad=new Set(),deadline=Date.now()+20000;
 for(let i=0;i<40&&Date.now()<deadline;i++){
  let ev=await c.readEvents({afterSequence:cur,methods,limit:1000,timeoutMs:1000});cur=ev.cursor;if(ev.truncated)throw Error('网络事件不完整');if(!ev.events.length)await new Promise(r=>setTimeout(r,250));
  for(let e of ev.events){let p=e.params||{};
   if(e.method==='Network.requestWillBeSent'&&p.request?.url?.split('?')[0]==='https://kns.cnki.net/kns8s/brief/grid'&&p.request.method==='POST')try{let b=new URLSearchParams(p.request.postData),j=JSON.parse(b.get('QueryJson')),items=j.QNode?.QGroup?.flatMap(g=>g.Items||[])||[];if(j.Resource==='ALMANAC'&&j.Products==='CYFD'&&j.Classid==='HHCPM1F8'&&b.get('pageNum')===String(page)&&items.some(x=>x.Field==='SU'&&x.Value===q))ids.add(p.requestId)}catch{}
   if(e.method==='Network.responseReceived'&&p.response?.status===200&&p.response?.mimeType==='text/html')ok.add(p.requestId);else if(e.method==='Network.responseReceived')bad.add(p.requestId);
   if(e.method==='Network.loadingFinished')done.add(p.requestId);if(e.method==='Network.loadingFailed')bad.add(p.requestId);
  }
  let id=[...ids].find(x=>ok.has(x)&&done.has(x));if(!id){if([...ids].some(x=>bad.has(x)))throw Error('知网分页请求失败');continue}
  let raw=await c.send('Network.getResponseBody',{requestId:id});if(raw.base64Encoded||typeof raw.body!=='string')throw Error('无法读取知网题录响应');
  for(let tries=0;tries<20;tries++){
   let state=await tab.playwright.evaluate(()=>({q:document.querySelector('#txt_search')?.value?.trim(),body:document.body.innerText,institution:document.querySelector('[title="浙江大学图书馆"]')?.getAttribute('title')||null,items:[...document.querySelectorAll('table.result-table-list tbody tr')].filter(x=>x.getClientRects().length).map(x=>{let a=x.querySelector('td.yearbook-title a');return {title:a?.innerText.trim(),url:a?.href,publication:x.querySelector('td.yearbook-chname')?.innerText.trim()||null,year:x.querySelector('td.yearbook-year')?.innerText.trim()||null,column:x.querySelector('td.yearbook-column')?.innerText.trim()||null}}).filter(x=>x.title&&x.url)}));
   let count=state.body.match(/共找到\s*([\d,]+)\s*条结果\s*(\d+)\/(\d+)/);
   if(state.q===q&&state.institution&&state.body.includes('检索范围： 年鉴 ')&&count&&Number(count[1].replaceAll(',',''))===total&&Number(count[2])===page&&state.items.length&&state.items.every(x=>{let v;try{v=new URL(x.url).searchParams.get('v')}catch{}return v&&raw.body.includes(v)}))return state.items.map((x,i)=>sanitize(x,(page-1)*20+i+1));
   await new Promise(r=>setTimeout(r,200));
  }
  throw Error('知网页面与分页响应不一致');
 }
 throw Error('未捕获匹配的知网分页响应（匹配请求 '+ids.size+'，成功响应 '+ok.size+'，完成事件 '+done.size+'）');
}
export async function searchCnkiYearbooks(tab,query,page=1){
 if(typeof query!=='string'||!query.trim()||query.length>100||/[\x00-\x1f]/.test(query))throw Error('关键词须为1–100字单行文本');
 if(!Number.isInteger(page)||page<1||page>2)throw Error('目前仅支持前2页');
 const q=query.trim();let state=await tab.playwright.evaluate(()=>({host:location.hostname,path:location.pathname,hasInput:!!document.querySelector('#txt_search'),institution:!!document.querySelector('[title="浙江大学图书馆"]')}));
 if(state.host!=='kns.cnki.net'||!state.path.startsWith('/kns8s/')||!state.hasInput||!state.institution)throw Error('请先打开有效的浙大年鉴结果页');
 const first=await cnkiYearbooksResponse(tab,q,async()=>{let i=await indexOf(tab,'txt_search','text field');await tab.setValue(i,q);await tab.pressKey(i,'Return')});
 if(page>1&&first.total<=(page-1)*20)throw Error('请求页超出站方总页数');
 let items=first.items.map((x,i)=>sanitize(x,i+1));for(let n=2;n<=page;n++)items=await nextPage(tab,q,n,first.total);
 return {source:'CNKI 年鉴浙大机构会话',institution:first.institution,query:q,page,page_size:20,total:first.total,items,note:'已有有效年鉴结果页会话中正常检索和顺序翻页；不输出来源链接参数，未验证逐篇全文。关键词按站方主题检索，结果及排序可能变化。'};
}
