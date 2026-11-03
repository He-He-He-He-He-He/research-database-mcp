/** 浙大电子书刊导航，标题开头检索当前页馆藏覆盖。 */
export async function ejournalFinderSearch(tab,keyword){
 if(typeof keyword!=='string'||!keyword.trim()||keyword.trim().length>100)throw Error('关键词须为 1–100 个字符');
 const query=keyword.trim();await tab.goto('https://gk4pb6yy8y.search.serialssolutions.com/?EMPTY_QUERY');
 await tab.playwright.locator('#SS_CFocusTag').fill(query); await tab.playwright.locator('input[type="submit"][value="搜索"]').first().click();
 await tab.playwright.locator('.SS_Holding .SS_JournalTitle').first().waitFor({state:'visible',timeoutMs:20000});
 const items=await tab.playwright.evaluate(()=>Array.from(document.querySelectorAll('.SS_HoldingsList > .SS_Holding')).filter(e=>e.getClientRects().length>0 && getComputedStyle(e).visibility==='visible').map(e=>({title:e.querySelector('.SS_JournalTitle')?.innerText.trim()||'',isbn:e.querySelector('.SS_BookISBN')?.innerText.trim()||'',author:e.querySelector('.SS_Authors')?.innerText.trim()||'',coverage:Array.from(e.querySelectorAll('.SS_HoldingData')).map(x=>x.innerText.trim().replace(/\s+/g,' ')).filter(Boolean)})).filter(x=>x.title));
 return {source:'浙大电子书刊导航',query,page:1,items,note:'标题开头搜索；读取当前页面可见馆藏条目，条目数可能与网站标示的记录数不同，无法保证一一对应；链接及具体访问权限未验证。'};
}
