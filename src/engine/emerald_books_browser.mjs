/** Emerald Books 目录首屏元数据，需遵守来源的使用条款。 */
export async function emeraldBooksSearch(tab,query) {
 if(typeof query!=='string'||!query.trim()||query.length>200) throw Error('关键词不能为空且不超过 200 字符');
 const u='https://www.emerald.com/books/search-results?'+new URLSearchParams({q:query.trim(),fl_SiteID:'5',page:'1',f_ContentType:'Book'});
 await tab.goto(u);
 await tab.playwright.locator('#searchContent .content-type-book h4 a').first().waitFor({state:'visible',timeoutMs:25000});
 return await tab.playwright.evaluate(()=>({source:'Emerald Books',institution:null,summary:document.querySelector('#searchContent')?.innerText.match(/\d+\s*-\s*\d+\s+of\s+[\d,]+/i)?.[0]||null,items:[...document.querySelectorAll('#searchContent .content-type-book')].filter(e=>e.getClientRects().length).map(e=>{const a=e.querySelector('h4 a');const avail=e.querySelector('[aria-label*="Available"], [aria-label*="Purchase"], [aria-label*="Open Access"]');return {title:a?.innerText.trim()||null,url:a?.href||null,access_label:avail?.getAttribute('aria-label')||null};}).filter(x=>x.title&&x.url),note:'当前页图书题录；不代表机构身份或全文授权。'}));
}
