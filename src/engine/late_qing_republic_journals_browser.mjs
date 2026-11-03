/* 全国报刊索引：晚清与民国期刊全文库首屏题录，未读取全文。 */
export async function lateQingRepublicJournalsSearch(tab,keyword){
 if(typeof keyword!=='string'||!keyword.trim()||keyword.length>100)throw Error('关键词须为 1–100 字');const query=keyword.trim();
 await tab.goto('https://www.cnbksy.com/search/advance?pid=22&isProduct=false');
 try{await tab.playwright.locator('#productTree_144_check.checkbox_true_full').waitFor({state:'attached',timeoutMs:20000});}catch{throw Error('初始范围与预期不符，停止以免误查其他子库');}
 await tab.playwright.locator('#productTree_144_check').click();await tab.playwright.locator('#productTree_1_check').click();
 const ids=await tab.playwright.evaluate(()=>[...document.querySelectorAll('#productTree span.chk')].filter(x=>x.className.includes('checkbox_true_full')).map(x=>x.id).sort());
 const allowed=['productTree_1_check','productTree_2_check','productTree_3_check','productTree_9_check','productTree_10_check'].sort();if(JSON.stringify(ids)!==JSON.stringify(allowed))throw Error('期刊子库勾选未通过核对');
 await tab.playwright.locator('#sf_1 input.advSearch').first().fill(query);await tab.playwright.getByRole('link',{name:'检 索',exact:true}).click();
 for(let i=0;i<8;i++){try{await tab.playwright.locator('#rt_1 a[href*="/search/detail/"]').first().waitFor({state:'visible',timeoutMs:20000});break;}catch{if(i===7)throw Error('未读取题录；可能无结果、登录或页面变化');}}
 const data=await tab.playwright.evaluate(()=>({institution:document.body.innerText.includes('[浙江大学图书馆]')?'浙江大学图书馆':null,items:[...document.querySelectorAll('#rt_1 table')].filter(e=>e.getClientRects().length).map(e=>{let a=e.querySelector('a[href*="/search/detail/"]');return a?{title:a.innerText.trim(),url:a.href,metadata:e.innerText.replace(a.innerText,'').split('整本浏览')[0].trim()}:null}).filter(Boolean)}));
 if(!data.items.length)throw Error('未读取期刊题录');return {source:'上图晚清民国期刊全文数据库',query,page:1,scope:'晚清期刊全文数据库及民国时期期刊全文数据库',...data,note:'首屏题录；资源库名称含全文，但未读取或验证全文权限。'};
}
