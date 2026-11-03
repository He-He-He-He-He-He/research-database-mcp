/** 中国经济社会大数据平台：统计资料题名搜索当前页，不读取表格或数值。 */
export async function cnkiStatisticalBooksSearch(tab,query){
 if(typeof query!=='string'||!query.trim()||query.length>100)throw Error('关键词需为1–100字');
 const u='https://data.cnki.net/statisticalData/index?'+new URLSearchParams({isSubcribe:'0',ky:query.trim()});
 await tab.goto(u);
 await tab.playwright.locator('h3 a[href*="yearBook/single"]').first().waitFor({state:'visible',timeoutMs:30000});
 const d=await tab.playwright.evaluate(()=>({institution:document.querySelector('[title="浙江大学图书馆"]')?.getAttribute('title')||null,items:[...document.querySelectorAll('h3 a[href*="yearBook/single"]')].filter(a=>a.getClientRects().length).map(a=>{const box=a.parentElement?.parentElement?.parentElement;return {title:a.innerText.trim(),url:a.href,years:[...box.querySelectorAll('p a')].filter(x=>x.getClientRects().length).map(x=>x.innerText.trim()).filter(x=>/^\d{4}$/.test(x))}})}));
 if(!d.items.length)throw Error('未读取统计资料题录');
 return {source:'中国经济社会大数据研究平台统计资料',query:query.trim(),...d,note:'当前页统计资料题名和页面展示年份，不获取具体统计表或数值；全文及数据权限未验证。'};
}
