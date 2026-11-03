/** IOPscience 浏览器当前页题录；不读取摘要或全文。 */
export async function iopSearch(tab, query) {
 if(typeof query!=='string'||!query.trim()||query.length>300) throw Error('关键词不能为空且不得超过 300 字符');
 const url='https://iopscience.iop.org/nsearch?'+new URLSearchParams({terms:query.trim()});
 await tab.goto(url);
 await tab.playwright.locator('#wd-iop-col-art-list > li .art-list-item-title a').first().waitFor({state:'visible',timeoutMs:25000});
 return await tab.playwright.evaluate(() => {
  const heading=document.querySelector('#results-title')?.innerText.trim()||null;
  const items=[...document.querySelectorAll('#wd-iop-col-art-list > li')].filter(x=>x.getClientRects().length).map(x=>{
   const a=x.querySelector('.art-list-item-title a');
   const meta=[...x.querySelectorAll('.art-list-item-meta')].map(p=>p.innerText.trim());
   const doi=[...x.querySelectorAll('.art-list-item-meta a')].find(a=>a.hostname==='doi.org');
   return {title:a?.innerText.trim()||null,url:a?.href||null,authors:meta[0]||null,publication:meta[1]||null,doi:doi?.href||null,access_label:x.querySelector('.eyebrow')?.innerText.trim()||null};
  }).filter(x=>x.title&&x.url);
  return {source:'IOPscience',institution:null,heading,items,note:'当前页题录；网站可能仅显示前 500 条，非全库总数。机构与全文权限未验证。'};
 });
}
