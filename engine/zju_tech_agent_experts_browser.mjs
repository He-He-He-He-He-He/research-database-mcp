/** School trial, one user-requested expert recommendation, current visible page only. */
export async function zjuTechnologyExpertRecommend(tab,query,limit=3){
 if(typeof query!=='string'||!query.trim()||query.length>80||/[\r\n\x00-\x1f]/.test(query))throw Error('query must be 1–80 ordinary characters');
 query=query.trim(); if(!Number.isInteger(limit)||limit<1||limit>5)throw Error('limit must be 1–5');
 const state=await tab.playwright.domSnapshot();
 if(!state.includes('浙江大学')||!state.includes('智推专家')||!state.includes('智能 推荐'))throw Error('Open the ZJU authenticated expert recommendation result page first');
 const field=tab.playwright.getByRole('textbox',{name:/请输入文本，进行成果转化数据查询/});
 const before=await tab.playwright.evaluate(()=>({query:document.querySelector('textarea')?.value||'',first:document.querySelector('.userInfo_right .name')?.textContent.trim()||''}));
 if(before.query===query)throw Error('Use a different query to confirm the result has refreshed');
 await field.fill(query); await tab.playwright.getByRole('button',{name:'智能 推荐'}).click();
 let updated=false;
 for(let i=0;i<45;i++){ await tab.playwright.waitForTimeout(1000); const first=await tab.playwright.evaluate(()=>document.querySelector('.userInfo_right .name')?.textContent.trim()||''); if(first&&first!==before.first){updated=true;break;} }
 if(!updated)throw Error('New result set could not be distinguished; no results returned');
 const d=await tab.playwright.evaluate((max)=>({host:location.hostname,path:location.pathname,institution:document.body.innerText.includes('浙江大学'),rows:[...document.querySelectorAll('.userInfo_right')].slice(0,max).map(e=>({name:e.querySelector('.name')?.textContent.trim()||'',affiliation:e.querySelector('.school .org_item')?.textContent.trim()||''}))}),limit);
 if(d.host!=='www.cstservice.cn'||d.path!=='/skillAgent/searchInfo'||!d.institution||!d.rows.length||d.rows.some(x=>!x.name))throw Error('ZJU expert results not verified');
 return {source:'产业科技创新服务平台 AI技术经纪人',query,items:d.rows,note:'ZJU IP trial until 2026-12-31; one recommendation of visible experts, not verified facts or complete search. Machine/AI usage license not confirmed.'};
}
