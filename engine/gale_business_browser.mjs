/* Gale Business: Insights：读取当前页面各类别的可见题录预览。 */
export async function galeBusinessSearch(tab,keyword){
 if(typeof keyword!=='string'||!keyword.trim()||keyword.length>100)throw Error('关键词需为 1–100 字');const q=keyword.trim();
 await tab.goto('https://go.gale.com/ps/start.do?p=GBIB&u=jiang');
 await tab.playwright.locator('#inputFieldValue_0').fill(q);await tab.playwright.locator('#quickSearchForm button').first().click();
 await tab.playwright.locator('#searchResults li.citation-view a[data-testid="document-title-link"]').first().waitFor({state:'visible',timeoutMs:30000});
 const d=await tab.playwright.evaluate(()=>({product:document.title,institution:document.querySelector('#libraryMenuButton')?.innerText.trim(),query:new URL(location.href).searchParams.get('inputFieldValues[0]'),groups:[...document.querySelectorAll('#searchResults [id$="_display_group"]')].filter(g=>g.getClientRects().length).map(g=>({name:g.querySelector('h2')?.innerText.replace(/\s+/g,' ').trim(),items:[...g.querySelectorAll('li.citation-view')].filter(e=>e.getClientRects().length&&e.querySelector('a[data-testid="document-title-link"]')).map(e=>{let a=e.querySelector('a[data-testid="document-title-link"]');return {id:e.dataset.id,title:a?.innerText.trim(),url:a?.href,citation:e.querySelector('.publication_citation')?.innerText.trim()||null};})})).filter(g=>g.items.length)}));
 if(!d.product.includes('Gale Business: Insights')||!d.institution?.includes('Zhejiang University')||d.query!==q||!d.groups.length||d.groups.some(g=>g.items.some(x=>!x.title||new URL(x.url).searchParams.get('prodId')!=='GBIB')))throw Error('未确认产品、机构或结果');
 return {source:'Gale Business: Insights',query:q,...d,note:'各类别当前可见预览，通常每类最多 3 条；不含公司预览，不等于完整分页；全文未验证。'};
}
