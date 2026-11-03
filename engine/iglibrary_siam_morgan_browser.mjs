/* 长煦书馆馆藏产品，读取筛选后的第一页书目；不操作阅读。 */
async function searchProduct(tab,keyword,slug,product){
 if(typeof keyword!=='string'||!keyword.trim()||keyword.length>100)throw Error('关键词需为 1–100 字');const q=keyword.trim();
 await tab.goto('https://portal.igpublish.com.cn/product/'+slug);
 await tab.playwright.getByRole('button',{name:'查看所有书'}).click();
 await tab.playwright.getByRole('textbox',{name:'Search input'}).fill(q);
 await tab.playwright.getByRole('textbox',{name:'Search input'}).press('Enter');
 await tab.playwright.locator('span.a2[role="heading"] highlight-em').first().waitFor({state:'visible',timeoutMs:30000});
 await tab.getAXState();
 const d=await tab.playwright.evaluate(()=>({url:location.href,institution:document.body.innerText.includes('浙江大学图书馆')?'浙江大学图书馆':null,filter:document.querySelector('#filter-content-v2-filters-product [role="checkbox"][aria-checked="true"]')?.getAttribute('aria-label')||null,items:[...document.querySelectorAll('span.a2[role="heading"][aria-level="2"]')].filter(x=>x.getClientRects().length).map(x=>{const p=x.parentElement?.parentElement;return {title:x.innerText.trim(),author:p?.children[1]?.innerText.trim()||null,publication:p?.children[2]?.innerText.trim()||null};})}));
 if(!d.institution||!d.filter?.startsWith(product+' (')||new URL(d.url).searchParams.get('keywords')!==q||!d.items.length||d.items.some(x=>!x.title))throw Error('机构、产品筛选或书目未确认；请检查页面是否加载完成');
 return {source:product,query:q,page:1,...d,note:'当前第一页题录；页面可能全文标识，未打开全文。'};
}
export const iglibrarySiamSearch=(tab,keyword)=>searchProduct(tab,keyword,'siam','Society for Industrial and Applied Mathematics');
export const iglibraryMorganSearch=(tab,keyword)=>searchProduct(tab,keyword,'morgan','Morgan & Claypool');
