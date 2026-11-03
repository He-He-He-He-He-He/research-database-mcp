/** Adis 期刊 Drugs 限刊单页题录。 */
export async function adisDrugsSearch(tab,query){
 if(typeof query!=='string'||!query.trim()||query.length>200)throw Error('关键词须为1–200字');
 const q=query.trim();const params=new URLSearchParams({'new-search':'true',query:q,'search-within':'Journal',sortBy:'relevance','facet-journal-id':'40265'});
 await tab.goto('https://link.springer.com/search?'+params);
 await tab.playwright.locator('.app-card-open__main').first().waitFor({state:'visible',timeoutMs:20000});
 const d=await tab.playwright.evaluate(()=>({url:location.href,total:(document.body.innerText.match(/Showing\s+\d[\d,]*-\d[\d,]*\s+of\s+([\d,]+)\s+results/i)||[])[1]||null,institution:document.body.innerText.includes('Zhejiang University Library')?'浙江大学图书馆':null,items:[...document.querySelectorAll('.app-card-open__main')].filter(c=>c.getClientRects().length).map(c=>({title:c.querySelector('h3 a')?.innerText.trim(),url:c.querySelector('h3 a')?.href,type:c.querySelector('[data-test="content-type"]')?.innerText.trim()||null,access:c.querySelector('[data-test="entitlements"]')?.innerText.trim()||null})).filter(x=>x.title)}));
 const p=new URL(d.url).searchParams;if(p.get('facet-journal-id')!=='40265'||p.get('query')!==q||!d.items.length)throw Error('未确认 Drugs 单刊筛选或结果');
 return {source:'Adis Drugs 期刊',query:q,...d,note:'仅 Drugs 单刊当前页题录，非全部 Adis 期刊；全文和单项访问未验证。'};
}
