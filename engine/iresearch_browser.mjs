/** 爱学术公开题录查询，仅读取当前可见首屏。 */
export async function iResearchSearch(tab,keyword){
 if(typeof keyword!=='string'||!keyword.trim()||keyword.trim().length>100)throw Error('关键词须为 1–100 个字符');
 const query=keyword.trim();await tab.goto('https://www.iresearchbook.cn/search/book/queryAll?onlyReadBuyed=0&searchField=all&searchValue='+encodeURIComponent(query)+'&officeId=&searchKey=');
 await tab.playwright.locator('.product-category-org-book-item .main-title').first().waitFor({state:'visible',timeoutMs:20000});
 const items=await tab.playwright.evaluate(()=>Array.from(document.querySelectorAll('.product-category-org-book-item')).filter(e=>e.getClientRects().length).map(e=>{const a=e.querySelector('.book-info a');return {title:e.querySelector('.main-title')?.innerText.trim()||'',url:a?.href||'',subtitle:Array.from(e.querySelectorAll('.sub-title')).filter(x=>x.getClientRects().length).map(x=>x.innerText.trim()),publication:e.querySelector('.page-info')?.innerText.trim()||''};}).filter(x=>x.title));
 return {source:'爱学术电子书',query,page:1,institution:null,items,note:'当前会话为访客，当前页公开题录；馆藏及全文权限未确认。'};
}
