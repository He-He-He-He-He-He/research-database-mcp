/* 中图易阅通：明确选择图书类型，首屏题录。 */
export async function cnpeBooksSearch(tab,keyword){
 if(typeof keyword!=='string'||!keyword.trim()||keyword.length>100)throw Error('关键词需为 1–100 字');
 const q=keyword.trim();await tab.goto('https://www.cnpereading.com/');
 await tab.playwright.locator('.searchInput .searchSelect input').click();await tab.playwright.locator('.el-select-dropdown__item').filter({hasText:'图书'}).first().click();
 await tab.playwright.getByPlaceholder('请输入内容',{exact:true}).first().fill(q);await tab.playwright.locator('.searchInput button.searchBtn').click();
 try{await tab.playwright.locator('.locks h3 a').first().waitFor({state:'visible',timeoutMs:20000});}catch{throw Error('未读取图书题录；可能无结果、验证或页面变化。');}
 const data=await tab.playwright.evaluate(()=>({type:document.querySelector('.searchInput .searchSelect input')?.value,institution:/浙江大学\s*阅读开启智慧之门/.test(document.body.innerText)?'浙江大学':null,items:[...document.querySelectorAll('.locks')].filter(e=>e.getClientRects().length).map(e=>{let a=e.querySelector('h3 a');return {title:a?.innerText.trim(),url:a?.href,metadata:[...e.querySelectorAll(':scope > p')].filter(p=>p.innerText.trim()).map(p=>p.innerText.trim()).join(' | ')}}).filter(x=>x.title)}));
 if(data.type!=='图书'||!data.items.length||data.items.some(x=>!x.url?.includes('/bookDetail/')))throw Error('图书筛选未通过核对，停止读取');return {source:'中图易阅通电子图书',query:q,page:1,...data,note:'当前页图书题录可能包含未订阅资源；机构名称不保证单项全文权限。'};
}
