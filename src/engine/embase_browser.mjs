/** 从已登录的 Embase 结果页读取当前页文章题录，不抓摘要/全文。 */
export async function embaseCurrentResults(tab,query){
 if(typeof query!=='string'||!query.trim()||query.length>100)throw Error('关键词需为1–100字');
 const q=query.trim().toLowerCase();
 const d=await tab.playwright.evaluate(()=>({url:location.href,query:document.querySelector('#search-query')?.value||'',heading:[...document.querySelectorAll('h3')].map(x=>x.innerText.trim()).find(x=>/results for search #/.test(x))||null,items:[...document.querySelectorAll('article')].filter(e=>e.getClientRects().length).map(e=>{let a=e.querySelector('[data-testid="title"] h2 a');return {title:a?.innerText.trim()||null,url:a?.href||null,authors:e.querySelector('[data-testid="authors"]')?.innerText.trim()||null,publication:e.querySelector('[data-testid="source"]')?.innerText.trim()||null}}).filter(x=>x.title&&x.url)}));
 if(!new URL(d.url).pathname.startsWith('/results')||!d.query.toLowerCase().includes(q)||!d.heading||!d.items.length)throw Error('未确认目标检索词的结果页面');
 return {source:'Embase',institution:null,...d,note:'读取当前结果页文章题录；查询可能经 Emtree 扩展，未验证全文或机构名称，遵守网站权利声明。'};
}
