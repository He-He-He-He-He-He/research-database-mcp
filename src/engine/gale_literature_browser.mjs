/* Gale Literature Resource Center：已建立浙大机构会话后读取默认类别首屏。 */
export async function galeLiteratureSearch(tab, keyword) {
 if(typeof keyword!=='string'||!keyword.trim()||keyword.length>100)throw Error('关键词需为 1–100 字');const q=keyword.trim();
 await tab.goto('https://go.gale.com/ps/start.do?u=jiang&p=LitRC&aty=shibboleth');
 await tab.playwright.locator('#inputFieldValue_0').fill(q);
 await tab.playwright.locator('#quickSearchForm button').first().click();
 await tab.playwright.locator('#searchResults li.citation-view a[data-testid="document-title-link"]').first().waitFor({state:'visible',timeoutMs:30000});
 const d=await tab.playwright.evaluate(()=>({product:document.title,institution:document.querySelector('#libraryMenuButton')?.innerText.trim(),query:new URL(location.href).searchParams.get('inputFieldValues[0]'),category:document.querySelector('.result-count_content-type')?.innerText.trim(),total:document.querySelector('.result-count_count')?.innerText.trim(),items:[...document.querySelectorAll('#searchResults li.citation-view')].filter(e=>e.getClientRects().length).map(e=>{const a=e.querySelector('a[data-testid="document-title-link"]');return {id:e.dataset.id,title:a?.innerText.trim(),url:a?.href,citation:e.querySelector('.publication_citation')?.innerText.trim()||null};})}));
 if(!d.product.includes('Gale Literature Resource Center')||!d.institution?.includes('Zhejiang University')||d.query!==q||!d.items.length||d.items.some(x=>!x.title||!new URL(x.url).searchParams.get('prodId')?.includes('LitRC')))throw Error('未确认产品、机构或结果');
 return {source:'Gale Literature Resource Center',query:q,page:1,...d,note:'仅默认结果分类第一页题录，其他分类和全文未验证。'};
}
