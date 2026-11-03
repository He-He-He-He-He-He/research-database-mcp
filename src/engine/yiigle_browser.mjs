/* 中华医学期刊：单页文献题录检索，不下载全文。 */
export async function yiigleSearch(tab,keyword){
 if(typeof keyword!=='string'||!keyword.trim()||keyword.length>100)throw Error('关键词需为 1–100 字');
 const u=new URL('https://www.yiigle.com/Paper/Search');u.search=new URLSearchParams({type:'',q:keyword.trim(),searchType:'pt'}).toString();await tab.goto(u.toString());
 try{await tab.playwright.locator('.s_searchResult_li_top a[title]').first().waitFor({state:'visible',timeoutMs:20000});}catch(_){throw Error('未读取题录，请检查无结果、登录、验证或页面变化。');}
 const data=await tab.playwright.evaluate(()=>({institution:document.body.innerText.includes('浙江大学图书馆')?'浙江大学图书馆':null,items:[...document.querySelectorAll('.s_searchResult_li')].map(e=>({title:e.querySelector('.s_searchResult_li_top a[title]')?.getAttribute('title'),authors:[...e.querySelectorAll('.author_sec a')].map(a=>a.getAttribute('title')||a.innerText.trim()),journal:e.querySelector('.zazhi_class')?.innerText.trim(),issue:e.querySelector('.zazhi_stage')?.innerText.trim(),url:e.querySelector('a[href*="rs.yiigle.com/cmaid/"]')?.href})).filter(x=>x.title)}));
 return {source:'中华医学期刊全文数据库',query:keyword.trim(),page:1,...data,note:'首屏文献题录，作者可能在页面被省略，全文权限未验证。'};
}
