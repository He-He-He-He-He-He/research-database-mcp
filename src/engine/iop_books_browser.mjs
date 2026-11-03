/** IOPscience book/chapter current-page metadata from one normal browser search. */
export async function iopBooksSearch(tab, keyword, submitSearch, limit=5){
 if(typeof keyword!=='string'||!keyword.trim()||keyword.length>150||typeof submitSearch!=='function'||!Number.isInteger(limit)||limit<1||limit>10)throw Error('需要关键词、单次检索回调和 1–10 条上限');
 const query=keyword.trim(); await submitSearch();
 const state=await tab.playwright.evaluate(()=>{
  const u=new URL(location.href);
  const items=Array.from(document.querySelectorAll('li.art-list-item')).map(el=>{
   const a=el.querySelector('h2.art-list-item-title a');
   const title=el.querySelector('[data-link-purpose-append]')?.getAttribute('data-link-purpose-append')?.trim()||'';
   const href=a?.getAttribute('href')||'';
   const authors=el.querySelector('h2 font')?null:Array.from(el.querySelectorAll('[itemprop="author"]')).map(x=>x.textContent.trim()).filter(Boolean);
   return {title,url:href.startsWith('/book/')?new URL(href,location.origin).href:'',authors};
  }).filter(x=>x.title&&x.url);
  return {host:u.hostname,path:u.pathname,query:u.searchParams.get('terms')||'',types:u.searchParams.getAll('pubType'),items};
 });
 if(state.host!=='iopscience.iop.org'||state.path!=='/nsearch'||state.query!==query||!state.types.includes('book')||!state.types.includes('chapter'))throw Error('电子书结果页、搜索词或范围不匹配');
 if(!state.items.length)throw Error('结果尚未加载或当前页没有可读取书目；空结果尚未验证');
 return {source:'IOPscience Books',query,items:state.items.slice(0,limit),note:'当前页书籍题录；网页检索范围包含书籍和章节，页面最多显示前 500 条结果，本接口不推断总数。作者为 null 表示浏览器翻译了页面，避免将译文误作原名。未验证学校机构身份或全文权限。'};
}
