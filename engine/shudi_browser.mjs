/* 书递电子图书：单页检索题录，不打开或下载全文。 */
export async function shudiSearch(tab,keyword){
 if(typeof keyword!=='string'||!keyword.trim()||keyword.length>100)throw Error('关键词需为 1–100 字');
 const u=new URL('https://www.elib.link/search');u.search=new URLSearchParams({searchKeyWord:keyword.trim()}).toString();await tab.goto(u.toString());
 try{await tab.playwright.locator('.search-book h3').first().waitFor({state:'visible',timeoutMs:15000});}catch(_){throw Error('未读取图书题录，请检查无结果、登录或页面变化。');}
 const items=await tab.playwright.evaluate(()=>[...document.querySelectorAll('.search-book')].map(e=>{const a=e.querySelector('a[href*="bookDetail"]');const p=[...e.querySelectorAll('p')].map(x=>x.innerText.trim());return {title:e.querySelector('h3')?.innerText.trim(),url:a?.href,author:p[0],date:p[1]};}).filter(x=>x.title));
 return {source:'书递中文电子图书平台',query:keyword.trim(),page:1,institution:null,items,note:'当前页全部图书题录，不代表本馆持有或全文授权。'};
}
