/** CADAL 蒋介石资料数据库首屏题录。 */
export async function cadalChiangSearch(tab,keyword){
 if(typeof keyword!=='string'||!keyword.trim()||keyword.trim().length>100||keyword.includes('^^'))throw Error('关键词须为 1–100 个字符且不能包含 ^^');
 const query=keyword.trim();const u=new URL('https://tecang.cadal.edu.cn/collection/list/G7pnWrTexNM=');u.search=new URLSearchParams({keyword:'all^^'+query+'^^wildcard'}).toString();await tab.goto(u.toString());
 await tab.playwright.locator('.content-box .title-box h3').first().waitFor({state:'visible',timeoutMs:20000});
 const items=await tab.playwright.evaluate(()=>Array.from(document.querySelectorAll('.content-box')).filter(e=>e.getClientRects().length&&e.querySelector('.title-box h3')).map(e=>({title:e.querySelector('.title-box h3')?.innerText.trim()||'',fields:Array.from(e.querySelectorAll('.fieldvalue1')).map(x=>x.innerText.trim())})).filter(x=>x.title));
 return {source:'蒋介石资料数据库',query,page:1,institution:null,items,note:'当前页题录；未确认机构身份和原文权限，无结果或页面变化可能超时。'};
}
