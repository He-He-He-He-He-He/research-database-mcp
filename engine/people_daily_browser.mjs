/** 人民日报图文数据库默认检索，仅读当前页题录。 */
export async function peopleDailySearch(tab,keyword){
 if(typeof keyword!=='string'||!keyword.trim()||keyword.trim().length>100)throw Error('关键词须为 1–100 个字符');
 const query=keyword.trim();await tab.goto('https://data.people.com.cn/rmrb/');
 await tab.playwright.locator('#queryStr').fill(query);await tab.playwright.locator('#queryStr').press('Enter');
 await tab.playwright.locator('.sreach_li h3 a').first().waitFor({state:'visible',timeoutMs:20000});
 const data=await tab.playwright.evaluate(()=>({institution:document.body.innerText.includes('浙江大学')?'浙江大学':null,items:Array.from(document.querySelectorAll('.sreach_li')).filter(e=>e.getClientRects().length).map(e=>{const a=e.querySelector('h3 a');return {title:a?.innerText.trim()||'',url:a?.href||'',issue:e.querySelector('.listinfo')?.innerText.trim()||''};}).filter(x=>x.title)}));
 return {source:'人民日报图文数据库',query,page:1,...data,note:'默认全部字段搜索当前页题录；正文及全文权限未验证。'};
}
