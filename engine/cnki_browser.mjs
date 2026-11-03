/** CNKI 默认主题检索当前页题录，不下载正文。 */
export async function cnkiSearch(tab,query){
 if(typeof query!=='string'||!query.trim()||query.length>200)throw Error('关键词不能为空且不得超过 200 字符');
 await tab.goto('https://www.cnki.net/');
 await tab.playwright.locator('#txt_SearchText').fill(query.trim());
 await tab.playwright.locator('#txt_SearchText').press('Enter');
 await tab.getAXState({emit:false});
 try{await tab.playwright.locator('table.result-table-list tbody tr td.name a').first().waitFor({state:'visible',timeoutMs:30000});}catch(e){const seen=await tab.playwright.evaluate(()=>document.querySelectorAll('table.result-table-list tbody tr td.name a').length);if(!seen){const state=await tab.playwright.evaluate(()=>document.body.innerText);if(/拖动下方拼图完成验证|安全验证/.test(state))throw Error('知网要求安全验证，需用户自行处理');throw Error('未取得结果；可能零结果或加载失败，请检查页面');}}
 const actual=await tab.playwright.evaluate(()=>document.querySelector('#txt_search')?.value||''); if(actual!==query.trim())throw Error('查询词未匹配');
 const out=await tab.playwright.evaluate(()=>({source:'CNKI 总库',institution:document.querySelector('[title="浙江大学图书馆"]')?.getAttribute('title')||null,items:[...document.querySelectorAll('table.result-table-list tbody tr')].filter(x=>x.getClientRects().length).map(x=>{let a=x.querySelector('td.name a');return {title:a?.innerText.trim()||null,url:a?.href||null,authors:x.querySelector('td.author')?.innerText.trim()||null,publication:x.querySelector('td.source')?.innerText.trim()||null,date:x.querySelector('td.date')?.innerText.trim()||null,type:x.querySelector('td.data')?.innerText.trim()||null}}).filter(x=>x.title&&x.url),note:'默认总库主题检索，仅当前页题录；全文权限未验证。零结果、验证或页面变化可能引起超时。'}));
 if(!out.items.length)throw Error('没有可验证的结果，可能为零结果或页面尚未加载');
 return out;
}
