import {validateGpdCounts} from './gpd_selection_response.mjs';
/** 尚唯 GPD 选型结果下一页的站方 JSON。 */
export async function gpdSelectionNextResponse(tab, query) {
 if(typeof query!=='string'||!query.trim()||query.length>100)throw Error('关键词需为 1–100 字'); const q=query.trim();
 const state=async()=>tab.playwright.evaluate(()=>({url:location.href,body:document.body.innerText,page:Number(document.querySelector('.el-pager .active')?.innerText)}));
 const valid=p=>{let u=new URL(p.url),key;try{key=decodeURIComponent(u.searchParams.get('key'))}catch{return false}return u.hostname==='gpd.sunwayinfo.com.cn' && u.pathname==='/list_selection' && p.body.includes('浙江大学') && key===q};
 let before=await state();if(!before.page||!valid(before))throw Error('请先完成相同关键词的机构选型检索');
 let c=await tab.capabilities.get('cdp');await c.send('Network.enable');let methods=['Network.requestWillBeSent','Network.responseReceived','Network.loadingFinished'],cur=(await c.readEvents({methods})).cursor;
 await tab.playwright.locator('button.btn-next').click();let ids=new Set(),ok=new Set(),done=new Set();
 for(let end=Date.now()+25000;Date.now()<end;){let e=await c.readEvents({afterSequence:cur,methods,limit:1000,timeoutMs:1000});cur=e.cursor;if(e.truncated)throw Error('网络事件不完整');for(let x of e.events){let p=x.params||{};if(x.method==='Network.requestWillBeSent'&&p.request?.url?.split('?')[0]==='https://gpd.sunwayinfo.com.cn/apis/gpd/data/searchListSec'&&p.request.method==='POST')ids.add(p.requestId);if(x.method==='Network.responseReceived'&&p.response?.status===200&&p.response?.mimeType==='application/json')ok.add(p.requestId);if(x.method==='Network.loadingFinished')done.add(p.requestId)}
 if(ids.size>1)throw Error('多个请求无法可靠关联');let id=[...ids].find(x=>ok.has(x)&&done.has(x));if(!id){await new Promise(r=>setTimeout(r,200));continue}let b=await c.send('Network.getResponseBody',{requestId:id});if(b.base64Encoded||!b.body)throw Error('无法读取响应');let v=JSON.parse(b.body),d=v.data?.result,p=await state();if(!valid(p)||p.page!==before.page+1||v.success!==true||d?.pageIndex!==p.page||d.pageSize!==12)throw Error('页面和响应不能对应');validateGpdCounts(d,p.page);
 return {source:'尚唯 GPD 学校会话产品选型',query:q,page:p.page,total:d.total,items:d.hits.map(x=>({id:x._id,name:x.series_name||'',brand:x.brand_name||null,cad_type:x.cad_type||null})),note:'单次下一页题录；请求加密，关联依据唯一响应及页面机构、关键词和页码；未验证图纸和详情。'};
 }throw Error('未捕获下一页响应');
}
