/* Literature Online 基本检索结果分组预览，仅当前页题录。 */
export async function proquestLionSearch(tab,keyword){
 if(typeof keyword!=='string'||!keyword.trim()||keyword.length>100)throw Error('关键词需为 1–100 字');const q=keyword.trim();await tab.goto('https://www.proquest.com/lion');
 try{await tab.playwright.locator('#searchTerm').fill(q);await tab.playwright.locator('#expandedSearch').click();await tab.playwright.locator('#lor_container h3 a').first().waitFor({state:'visible',timeoutMs:20000});}catch{throw Error('未读取结果；请检查机构会话、Cookie 提示、无结果或网页变化。');}
 const data=await tab.playwright.evaluate(()=>({institution:document.body.innerText.includes('ZHEJIANG UNIVERSITY LIBRARY')?'ZHEJIANG UNIVERSITY LIBRARY':null,items:[...document.querySelectorAll('#lor_container div[id*="_mlditem"]')].filter(e=>e.getClientRects().length).map(e=>{let a=e.querySelector('h3 a');return a?{group:e.id.split('_')[0],title:a.innerText.trim(),url:a.href}:null}).filter(Boolean)}));
 if(!locationCheck(data)||!data.items.length)throw Error('未确认 Literature Online 结果');return {source:'ProQuest Literature Online',query:q,page:1,...data,note:'各结果分组首屏预览，通常每组最多 3 项；不是完整分页结果。未读取全文。'};
}
function locationCheck(data){return !!data.institution}
