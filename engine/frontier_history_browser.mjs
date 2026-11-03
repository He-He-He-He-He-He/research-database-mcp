/** 校园网边疆史地研究资料库：默认任意类型单页题录。 */
export async function frontierHistorySearch(tab,keyword){
 if(typeof keyword!=='string'||!keyword.trim()||keyword.trim().length>100)throw Error('关键词须为 1–100 个字符');
 const query=keyword.trim(); await tab.goto('http://10.15.61.59:8080/');
 await tab.playwright.locator('input[name="keyword"]').fill(query); await tab.playwright.locator('input[value="search"]').click();
 await tab.playwright.locator('a[href^="literature/"]').first().waitFor({state:'visible',timeoutMs:20000});
 const items=await tab.playwright.evaluate(()=>Array.from(document.querySelectorAll('a[href^="literature/"]')).map(a=>({title:a.innerText.trim(),url:a.href})).filter(x=>x.title));
 return {source:'中国边疆史地研究资料数据库',query,page:1,items,note:'校园内部资源，依赖当前网络及机构会话；全文未验证，无结果或改版可能超时。'};
}
