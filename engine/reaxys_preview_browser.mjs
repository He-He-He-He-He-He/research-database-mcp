/** 读取当前 Reaxys 已展开的文献预览，不导航、不提交搜索。 */
export async function reaxysDocumentsPreview(tab, query){
 if(typeof query!=='string'||!query.trim()||query!==query.trim()||query.length>100)throw Error('请输入当前页面的检索词');
 const d=await tab.playwright.evaluate(()=>{
  const u=new URL(location.href),q=document.querySelector('.quick-results-heading__query')?.innerText.trim();
  const heading=[...document.querySelectorAll('h2')].find(x=>x.innerText.trim()==='Documents');const card=heading?.closest('.quick-results-preview__item');
  const count=card?.querySelector('.results-preview__block--count')?.innerText.trim().replaceAll(',','');
  const rows=[...card?.querySelectorAll('.quick-results-preview__item_preview-citations li.e2e-results-list-item')||[]].map(e=>({title:e.querySelector('button.e2e-document-action-title h4')?.innerText.trim()||null,authors:e.querySelector('.rx-element-authors')?.innerText.replace(/\s*;\s*/g,'; ').trim()||null,citation:e.querySelector('.document-journals')?.innerText.replace(/\s*\(opens in a new window\)\s*/g,'').trim()||null}));
  return {host:u.hostname,hash:u.hash,q,total:count&&/^\d+$/.test(count)?Number(count):null,rows};
 });
 if(d.host!=='www.reaxys.com'||!d.hash.startsWith('#/search/quick/results')||d.q!==query||d.total===null||!d.rows.length||d.rows.length>3||d.rows.some(x=>!x.title))throw Error('当前标签不是指定查询的已展开 Documents 预览，或结果尚未加载');
 return {source:'Reaxys',query,total:d.total,items:d.rows,note:'当前账号结果页的最多三条文献预览题录；非全文或完整结果。'};
}
