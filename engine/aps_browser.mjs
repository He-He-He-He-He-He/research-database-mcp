/** APS Journals 可见题录读取器。 */
export async function apsPage(tab,query) {
 if(typeof query!=='string'||!query.trim()) throw Error('关键词不能为空');
 const p=new URLSearchParams({sort:'relevance',clauses:JSON.stringify([{operator:'AND',field:'all',value:query.trim()}])});
 await tab.goto('https://journals.aps.org/search/results?'+p);
 await tab.playwright.locator('a[data-gtm-identifier]').first().waitFor({state:'visible',timeoutMs:25000});
 return await tab.playwright.evaluate(()=>({source:'APS Journals',institution:null,total:(document.body.innerText.match(/\d+\s*-\s*\d+\s+of\s+([\d,]+)\s+Results/i)||[])[1]||null,items:[...document.querySelectorAll('a[data-gtm-identifier]')].filter(a=>a.getClientRects().length).map(a=>{let c=a.parentElement.parentElement;let p=[...c.querySelectorAll('p')].map(x=>x.innerText.trim());return {title:a.innerText.trim(),url:a.href,doi:a.getAttribute('data-gtm-identifier'),journal:c.querySelector('.article-feature-tag')?.innerText.trim()||null,authors:p[0]||null,publication:p[1]||null};}).filter(x=>x.title)}));
}
