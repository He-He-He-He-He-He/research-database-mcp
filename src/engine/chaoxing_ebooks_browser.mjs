/* 超星汇雅电子书：书名单页题录，不打开阅读器。 */
export async function chaoxingEbooksSearch(tab,keyword){
 if(typeof keyword!=='string'||!keyword.trim()||keyword.length>100)throw Error('关键词需为 1–100 字');
 const q=keyword.trim(),u=new URL('https://www.sslibrary.com/book/search');u.search=new URLSearchParams({fromType:'portal',field:'1',sw:q,terlg:'1'}).toString();await tab.goto(u.toString());
 try{await tab.playwright.locator('ul.zli_item h2 a').first().waitFor({state:'visible',timeoutMs:20000});}catch{throw Error('未读取图书题录；可能无结果、登录、验证或页面变化。');}
 const data=await tab.playwright.evaluate(()=>({institution:/欢迎来自\s*浙江大学\s*的用户/.test(document.body.innerText)?'浙江大学':null,items:[...document.querySelectorAll('ul.zli_item')].filter(e=>e.getClientRects().length).map(e=>{let a=e.querySelector('h2 a'),fields={};for(let p of e.querySelectorAll('p')){let l=p.querySelector('em.zli_i_field');if(l)fields[l.innerText.trim()]=p.innerText.replace(l.innerText,'').trim();}return {title:a?.innerText.trim(),url:a?.href,author:fields['作者']||null,date:fields['出版日期']||null,publisher:fields['出版社']||null,pages:fields['页数']||null,classification:fields['中图分类号']||null,isbn:fields['ISBN']||null};}).filter(x=>x.title)}));
 if(!data.items.length)throw Error('未读取当前页题录');return {source:'超星汇雅电子书',query:q,page:1,...data,note:'书名搜索当前页题录；机构身份不保证单本阅读权限，未下载全文。'};
}
