/* 中图易阅通：普通搜索首屏题录，不读取全文。 */
export async function cnpeReadingSearch(tab,keyword){
 if(typeof keyword!=='string'||!keyword.trim()||keyword.length>100)throw Error('关键词需为 1–100 字');
 const q=keyword.trim();await tab.goto('https://www.cnpereading.com/');await tab.playwright.getByPlaceholder('请输入内容',{exact:true}).first().fill(q);await tab.playwright.locator('.searchInput button.searchBtn').click();
 try{await tab.playwright.locator('.locks h3 a').first().waitFor({state:'visible',timeoutMs:20000});}catch{throw Error('未读取题录；可能无结果、验证或页面变化，请检查网页。');}
 const data=await tab.playwright.evaluate(()=>({institution:/浙江大学\s*阅读开启智慧之门/.test(document.body.innerText)?'浙江大学':null,items:[...document.querySelectorAll('.locks')].filter(e=>e.getClientRects().length).map(e=>{let a=e.querySelector('h3 a');return {title:a?.innerText.trim(),url:a?.href,metadata:[...e.querySelectorAll(':scope > p')].filter(p=>p.innerText.trim()).map(p=>p.innerText.trim()).join(' | ')}}).filter(x=>x.title)}));
 if(!data.items.length)throw Error('未读取当前页题录');return {source:'中图易阅通',query:q,page:1,...data,note:'默认全部资源当前页题录，包含未订阅项；机构名称不保证单项全文权限。'};
}
