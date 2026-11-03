/** ScienceDirect 丛书目录的当前页标题，不涉及正文。 */
export async function scienceDirectSeriesSearch(tab, query) {
 if(typeof query!=='string'||!query.trim()||query.length>200) throw Error('关键词不能为空且不超过 200 字符');
 const u='https://www.sciencedirect.com/browse/journals-and-books?'+new URLSearchParams({contentType:'BS',searchPhrase:query.trim()});
 await tab.goto(u);
 await tab.playwright.locator('#first-result-item').first().waitFor({state:'visible',timeoutMs:25000});
 return await tab.playwright.evaluate(()=>{
  const items=[...document.querySelectorAll('li.js-publication')].map(x=>{let a=x.querySelector('a.js-publication-title');return {title:a?.innerText.trim()||null,url:a?.href||null,type:x.querySelector('.js-publication-content-type')?.innerText.trim()||null};}).filter(x=>x.title&&x.url&&x.type==='Book series');
  return {source:'ScienceDirect Book series',institution:document.body.innerText.includes('Zhejiang University Library')?'Zhejiang University Library':null,heading:document.querySelector('main h1')?.innerText.trim()||null,items,note:'只返回当前页丛书名称与链接，非章级检索或已验证全文权限。'};
 });
}

/** ScienceDirect 图书目录当前页（不包括丛书条目、教材等其他类型）。 */
export async function scienceDirectBooksSearch(tab, query) {
 if(typeof query!=='string'||!query.trim()||query.length>200) throw Error('关键词不能为空且不超过 200 字符');
 const u='https://www.sciencedirect.com/browse/journals-and-books?'+new URLSearchParams({contentType:'BK',searchPhrase:query.trim()});
 await tab.goto(u);
 await tab.playwright.locator('#first-result-item').first().waitFor({state:'visible',timeoutMs:25000});
 return await tab.playwright.evaluate(()=>{
  const items=[...document.querySelectorAll('li.js-publication')].map(x=>{let a=x.querySelector('a.js-publication-title');return {title:a?.innerText.trim()||null,url:a?.href||null,type:x.querySelector('.js-publication-content-type')?.innerText.trim()||null,publication:x.querySelector('.publication-text')?.innerText.trim()||null};}).filter(x=>x.title&&x.url&&x.type==='Book');
  return {source:'ScienceDirect Books',institution:document.body.innerText.includes('Zhejiang University Library')?'Zhejiang University Library':null,heading:document.querySelector('main h1')?.innerText.trim()||null,items,note:'只返回当前页图书名称与链接；非章节检索或已验证全文权限。'};
 });
}
