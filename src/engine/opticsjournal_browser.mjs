/* 中国光学期刊网：标题快速检索，仅返回当前页论文题录。 */
export async function opticsJournalSearch(tab,keyword){
 if(typeof keyword!=='string'||!keyword.trim()||keyword.length>100) throw Error('关键词需为 1–100 字');
 const u=new URL('https://www.opticsjournal.net/Articles/SimpleSearch');u.search=new URLSearchParams({kt:'A',kw:keyword.trim()}).toString();
 await tab.goto(u.toString());
 try{await tab.playwright.locator('.item.article .art-title[data-aid]').first().waitFor({state:'visible',timeoutMs:15000});}catch(_){throw Error('未读取到论文，请检查无结果、登录、验证或页面变化。');}
 const items=await tab.playwright.evaluate(()=>[...document.querySelectorAll('.item.article')].map(e=>{const a=e.querySelector('.art-title[data-aid]');return {title:a?.innerText.trim(),id:a?.dataset.aid,url:a?.href,authors:[...e.querySelectorAll('.authors .au-link')].map(x=>x.innerText.trim())};}).filter(x=>x.title));
 return {source:'中国光学期刊网',query:keyword.trim(),page:1,institution:null,items,note:'当前页题名和页面展示作者；作者可能被网站省略，全文权限未验证。'};
}
