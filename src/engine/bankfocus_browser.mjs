/** BankFocus 当前机构会话的搜索建议；调用方须先通过图书馆入口进入搜索页。 */
export async function bankfocusQuickSearch(tab,query) {
 if(typeof query!=='string'||!query.trim()) throw Error('关键词不能为空');
 query=query.trim();
 const host=await tab.playwright.evaluate(()=>location.hostname);
 if(host!=='bankfocus-r1.bvdinfo.com') throw Error('请先打开 BankFocus');
 const prior=await tab.playwright.evaluate(()=>({q:document.querySelector('#search')?.value,token:document.querySelector('#quicksearch-results ul')?.getAttribute('data-token')}));
 if(prior.q===undefined) throw Error('请先打开 BankFocus 的 Search 页面');
 if(prior.q===query) await tab.playwright.locator('#search').fill('');
 await tab.playwright.locator('#search').fill(query);
 for(let i=0;i<15;i++){
  const result=await tab.playwright.evaluate(({query,token})=>{
   const input=document.querySelector('#search'),box=document.querySelector('#quicksearch-results'),ul=box?.querySelector('ul');
   if(input?.value!==query || !ul || ul.getAttribute('data-token')===token || !box.getClientRects().length) return null;
   const items=[...ul.querySelectorAll('a[data-search-select-one]')].filter(a=>a.getClientRects().length).map(a=>({name:a.querySelector('.name')?.innerText.trim(),location:a.querySelector('.location')?.innerText.trim()||null,type:a.querySelector('.size')?.innerText.trim()||null,id:a.getAttribute('data-parambvdid')||null,financial:a.querySelector('.turnover')?.innerText.trim()||null})).filter(x=>x.name);
   return {source:'BankFocus 快速建议',institution:/@zju\.edu\.cn/i.test(document.body.innerText)?'Zhejiang University（机构账号）':null,total:ul.getAttribute('data-search-count'),items};
  },{query,token:prior.token});
  if(result?.items?.length) return result;
  await new Promise(resolve=>setTimeout(resolve,500));
 }
 throw Error('搜索建议未加载或无可确认结果');
}
