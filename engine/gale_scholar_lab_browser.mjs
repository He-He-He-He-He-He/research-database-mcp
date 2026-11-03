/** Gale Digital Scholar Lab 已登录机构及个人会话的首页检索。 */
export async function galeScholarLabSearch(tab,keyword){
 if(typeof keyword!=='string'||!keyword.trim()||keyword.trim().length>100)throw Error('关键词需为 1–100 字');
 const q=keyword.trim();
 const pre=await tab.playwright.evaluate(()=>({host:location.hostname,product:new URL(location.href).searchParams.get('prodId')||new URL(location.href).searchParams.get('p'),institution:document.querySelector('#libraryMenuButton')?.innerText,hasSearch:!!document.querySelector('#quickSearchTermInput')}));
 if(pre.host!=='go.gale.com'||pre.product!=='DSLAB'||!pre.institution?.includes('Zhejiang University')||!pre.hasSearch)throw Error('请先打开已登录的浙江大学 Digital Scholar Lab 页面');
 await tab.playwright.locator('#quickSearchTermInput').fill(q);
 await tab.playwright.locator('#quickSearchSubmit').click();
 await tab.playwright.locator('#searchResults li.citation-view a[data-testid="document-title-link"]').first().waitFor({state:'visible',timeoutMs:30000});
 const d=await tab.playwright.evaluate(()=>({product:new URL(location.href).searchParams.get('prodId'),query:new URL(location.href).searchParams.get('quickSearchTerm'),institution:document.querySelector('#libraryMenuButton')?.innerText?.trim(),title:document.title,items:[...document.querySelectorAll('#searchResults li.citation-view')].filter(e=>e.getClientRects().length).map(e=>({id:e.dataset.id,title:e.querySelector('a[data-testid="document-title-link"]')?.innerText.trim(),archive:e.dataset.attributionName,author:e.querySelector('.author .value')?.innerText.trim()||null,ocr:e.querySelector('.ocr-confidence-level .definition')?.innerText.trim()||null}))}));
 if(d.product!=='DSLAB'||d.query!==q||!d.institution?.includes('Zhejiang University')||!d.items.length||d.items.some(x=>!x.id||!x.title))throw Error('未确认机构、关键词或结果');
 return {source:'Gale Digital Scholar Lab',query:q,page:1,institution:d.institution,items:d.items,note:'已登录机构和个人会话的当前页题录；未验证全文、分析或批量导出。'};
}
