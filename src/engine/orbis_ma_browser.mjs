/** Orbis M&A 当前机构会话可见交易建议，调用方先进入 Search 页面。 */
export async function orbisMaQuickSearch(tab,query){
 if(typeof query!=='string'||!query.trim()) throw Error('关键词不能为空'); query=query.trim();
 const prior=await tab.playwright.evaluate(()=>({host:location.hostname,q:document.querySelector('#search')?.value,token:document.querySelector('#quicksearch-results ul')?.getAttribute('data-token')}));
 if(prior.host!=='orbismanda-r1.bvdinfo.com'||prior.q===undefined) throw Error('请先打开 Orbis M&A 的 Search 页面');
 if(prior.q===query) await tab.playwright.locator('#search').fill('');
 await tab.playwright.locator('#search').fill(query);
 for(let i=0;i<15;i++){
  const result=await tab.playwright.evaluate(({query,token})=>{
   const box=document.querySelector('#quicksearch-results'),ul=box?.querySelector('ul');
   if(document.querySelector('#search')?.value!==query||!ul||ul.getAttribute('data-token')===token||!box.getClientRects().length) return null;
   const items=[...ul.querySelectorAll('a[data-search-select-one]')].filter(a=>a.getClientRects().length).map(a=>({name:a.querySelector('.name')?.innerText.trim(),id:a.getAttribute('data-parambvdid')||null,fields:Object.fromEntries([...a.querySelectorAll('div')].filter(d=>d.querySelector(':scope > .quickLabel')).map(d=>[d.querySelector('.quickLabel')?.innerText.replace(/\s*:\s*$/,'').trim(),d.querySelector('.quickLabel + span')?.innerText.trim()||null]))})).filter(x=>x.name);
   return {source:'Orbis M&A 交易快速建议',institution:/@zju\.edu\.cn/i.test(document.body.innerText)?'Zhejiang University（机构账号）':null,total:ul.getAttribute('data-search-count'),items};
  },{query,token:prior.token});
  if(result?.items?.length) return result;
  await new Promise(resolve=>setTimeout(resolve,500));
 }
 throw Error('搜索建议未加载或无可确认结果');
}
