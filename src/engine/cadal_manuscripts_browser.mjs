/* CADAL 中国写本文献：当前页题录，仅读取字段和标题。 */
export async function cadalManuscriptSearch(tab,keyword){
 if(typeof keyword!=='string'||!keyword.trim()||keyword.length>100||keyword.includes('^^'))throw Error('关键词需为 1–100 字且不能包含 ^^');
 const u=new URL('https://tecang.cadal.edu.cn/collection/list/ilK_dP_LJ34=');u.search=new URLSearchParams({keyword:'all^^'+keyword.trim()+'^^wildcard'}).toString();await tab.goto(u.toString());
 try{await tab.playwright.locator('.content-box .title-box h3').first().waitFor({state:'visible',timeoutMs:15000});}catch(_){throw Error('未读取写本题录，请检查无结果、登录或页面变化。');}
 const items=await tab.playwright.evaluate(()=>[...document.querySelectorAll('.content-box')].filter(e=>e.querySelector('.title-box h3')).map(e=>({title:e.querySelector('.title-box h3')?.innerText.trim(),fields:[...e.querySelectorAll('.fieldvalue1')].map(x=>x.innerText.trim())})));
 return {source:'中国写本文献数字资源库',query:keyword.trim(),page:1,institution:null,items,note:'当前页题录字段；未确认机构识别或影像权限。'};
}
