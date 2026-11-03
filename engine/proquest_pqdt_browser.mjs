/* ProQuest ProQuest Dissertations & Theses Global：已有浙大机构会话，读取结果页题录。 */
export async function proquestPqdtSearch(tab, keyword) {
 if(typeof keyword!=='string'||!keyword.trim()||keyword.length>100) throw Error('关键词需为 1–100 字');
 const q=keyword.trim();
 await tab.goto('https://www.proquest.com/pqdtglobal');
 await tab.playwright.locator('#searchTerm').fill(q);
 await tab.playwright.locator('#expandedSearch').click();
 await tab.playwright.locator('#lor_container [id^="mlditem"] h3 a').first().waitFor({state:'visible',timeoutMs:30000});
 let data;
 for(let attempt=0;attempt<8;attempt++){
 data=await tab.playwright.evaluate(()=>({query:document.querySelector('#searchTerm')?.value||null,path:location.pathname,institution:document.body.innerText.includes('ZHEJIANG UNIVERSITY LIBRARY')?'ZHEJIANG UNIVERSITY LIBRARY':null,total:document.querySelector('#pqResultsCount')?.innerText.trim()||null,items:[...document.querySelectorAll('#lor_container [id^="mlditem"]')].filter(e=>e.getClientRects().length).map(e=>{const a=e.querySelector('h3 a'); const copy=e.querySelector('.resultHeader'); return {title:a?.innerText.trim(),url:a?.href,author:copy?.querySelector('.scholUnivAuthors')?.innerText.trim()||null,citation:copy?.querySelector('.jnlArticle')?.innerText.trim()||null,databaseHints:[...e.querySelectorAll('.content-item-links a[title]')].map(x=>x.title).filter(x=>x.includes('来自于'))};})}));
 if(data.path.startsWith('/pqdtglobal/results/')&&data.query===q&&data.institution&&data.items.length&&!data.items.some(x=>!x.title||!x.databaseHints.length))break;
 await tab.getAXState({emit:false});
 }
 if(!data.path.startsWith('/pqdtglobal/results/')||data.query!==q||!data.institution||!data.items.length||data.items.some(x=>!x.title||!x.databaseHints.length))throw Error('未确认检索词、机构、集合或结果来源');
 return {source:'ProQuest Dissertations & Theses Global',query:q,page:1,...data,note:'集合包含多个子库；每项来源提示可能同时包括其他数据库。仅当前页题录，全文未验证。'};
}
