import {validateSunwayCounts} from './sunway_report_response.mjs';
/** 尚唯科技报告已检索结果的下一页响应，须有效浙大会话。 */
export async function sunwayReportNextResponse(tab, query) {
 if(typeof query!=='string'||!query.trim()||query.length>100)throw Error('关键词需为 1–100 字'); const q=query.trim();
 const state=async()=>tab.playwright.evaluate(()=>({url:location.href,body:document.body.innerText,page:Number(document.querySelector('.el-pager .active')?.innerText)}));
 const validate=p=>{let u=new URL(p.url),cond;try{cond=JSON.parse(decodeURIComponent(u.searchParams.get('tagCondition')))}catch{return false}let a=cond.condition;return u.hostname==='bg.sunwayinfo.com.cn' && u.pathname==='/report_list' && /浙江大学\s+欢迎访问/.test(p.body) && a?.length===1 && a[0].key===q && JSON.stringify(a[0].field)===JSON.stringify(['title','title_zh','title_en']);};
 let before=await state();if(!before.page||!validate(before))throw Error('请先完成相同关键词的机构报告检索');
 let c=await tab.capabilities.get('cdp');await c.send('Network.enable');let methods=['Network.requestWillBeSent','Network.responseReceived','Network.loadingFinished'];let cur=(await c.readEvents({methods})).cursor;
 await tab.playwright.locator('button.btn-next').click();let ids=new Set(),ok=new Set(),done=new Set();
 for(let deadline=Date.now()+25000;Date.now()<deadline;){let e=await c.readEvents({afterSequence:cur,methods,limit:1000,timeoutMs:1000});cur=e.cursor;if(e.truncated)throw Error('事件不完整');for(let x of e.events){let p=x.params||{};if(x.method==='Network.requestWillBeSent'&&p.request?.url==='https://bg.sunwayinfo.com.cn/apis/kjbg/data/searchListSec'&&p.request.method==='POST')ids.add(p.requestId);if(x.method==='Network.responseReceived'&&p.response?.status===200&&p.response?.mimeType==='application/json')ok.add(p.requestId);if(x.method==='Network.loadingFinished')done.add(p.requestId)}
 if(ids.size>1)throw Error('出现多个响应，无法可靠关联');let id=[...ids].find(x=>ok.has(x)&&done.has(x));if(!id){await new Promise(r=>setTimeout(r,200));continue}let b=await c.send('Network.getResponseBody',{requestId:id});if(b.base64Encoded||!b.body)throw Error('无法读取响应');let d=JSON.parse(b.body),p=await state();if(!validate(p)||p.page!==before.page+1||d.success!==true||d.data?.pageIndex!==p.page||d.data.pageSize!==10)throw Error('页面与响应不能对应');validateSunwayCounts(d.data,p.page);
 return {source:'尚唯科技报告机构会话',query:q,page:p.page,total:d.data.total,items:d.data.hits.map(x=>({id:x._id,title:x.title||'',translated_title:x.title_zh||null,authors:x.author||[],report_number:x.report_number||[],date:x.pub_date||null})),note:'单次下一页题录；请求加密，关联依据唯一响应及页面机构、条件、页码。未验证全文。'};
 }throw Error('未捕获下一页响应');
}
