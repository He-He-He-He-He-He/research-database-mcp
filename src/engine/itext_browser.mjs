/** 爱教材平台首屏题录，使用已绑定 CUA 浏览器 Tab。 */
export async function itextSearch(tab,keyword){
 if(typeof keyword!=='string'||!keyword.trim()||keyword.trim().length>100)throw Error('关键词须为 1–100 个字符');
 const query=keyword.trim(); await tab.goto('https://www.itextbook.cn/');
 await tab.playwright.locator('#content').fill(query); await tab.playwright.locator('#content').press('Enter');
 await tab.playwright.locator('.book-info .title a').first().waitFor({state:'visible',timeoutMs:20000});
 const data=await tab.playwright.evaluate(()=>({institution:document.body.innerText.includes('浙江大学')?'浙江大学':null,items:Array.from(document.querySelectorAll('li')).filter(e=>e.querySelector('.book-info .title a')).map(e=>{let a=e.querySelector('.book-info .title a');return {title:a.innerText.trim(),url:a.href,author:e.querySelector('.start-group')?.innerText.trim()||'',purchaseStatus:e.querySelector('.book-img')?.innerText.trim()||null};})}));
 return {source:'爱教材平台',query,page:1,...data,note:'当前页题录；购买标记仅取页面可见信息，阅读权限未验证。'};
}
