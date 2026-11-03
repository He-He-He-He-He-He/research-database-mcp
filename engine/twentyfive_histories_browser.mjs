/** 二十五史研习系统：搜索结果按文献汇总，非全文抽取。 */
export async function historiesSearch(tab,keyword){
 if(typeof keyword!=='string'||!keyword.trim()||keyword.length>100) throw Error('关键词须为 1–100 字');
 const query=keyword.trim();
 await tab.goto('http://www.chinabooktrading.com:81/h25/');
 await tab.playwright.locator('input.keywords').fill(query); await tab.playwright.locator('input.keywords').press('Enter');
 for(let i=0;i<3;i++){try{await tab.playwright.locator('a[href*="/QUERY/"]').filter({hasText:'中共檢索到'}).first().waitFor({state:'visible',timeoutMs:20000});break;}catch(e){if(i===2)throw e;}}
 const items=await tab.playwright.evaluate(()=>Array.from(document.querySelectorAll('a[href*="/QUERY/"]')).filter(e=>e.innerText.includes('中共檢索到')).map(e=>({summary:e.innerText.trim(),url:e.href})));
 return {source:'二十五史研习系统',query,institution:null,items,note:'搜索结果按文献聚合的数量与链接，不读取正文；页面未显示机构身份。'};
}
