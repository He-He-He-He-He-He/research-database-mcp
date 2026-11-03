/** Max Planck 国际法百科，查询合并后的 MPIL 产品；只读取当前页元数据。 */
export async function maxPlanckInternationalLawPage(tab,query) {
  if(typeof query!=='string'||!query.trim()) throw Error('关键词不能为空');
  const p=new URLSearchParams({sfam:'',q:query.trim(),prd:'MPIL',searchBtn:'Search'});
  await tab.goto('https://opil.ouplaw.com/search?'+p);
  await tab.playwright.locator('body').waitFor({state:'visible',timeoutMs:25000});
  return await tab.playwright.evaluate(()=>{
    const body=document.body.innerText;
    if(!body.includes('Search Results')) throw Error('未确认检索结果页');
    const items=[...document.querySelectorAll('.contentItem.standardResult')].filter(c=>c.getClientRects().length).map(c=>{
      const data=Object.fromEntries([...c.querySelectorAll('dl.metadata')].map(d=>[d.querySelector('dt')?.innerText.trim(),d.querySelector('dd')?.innerText.trim()]));
      return {title:c.querySelector('h2.itemTitle a')?.innerText.trim(),url:c.querySelector('h2.itemTitle a')?.href,authors:c.querySelector('.itemAuthor')?.innerText.trim()||null,type:data['Content type']||null,product:data.Product||null,module:data.Module||null,subjects:data['Subject(s)']||null,access:c.classList.contains('hasAccess')?'hasAccess':c.classList.contains('locked')?'locked':null};
    }).filter(x=>x.title&&x.product?.includes('Max Planck Encyclopedias of International Law'));
    return {source:'Max Planck 国际法百科（MPIL 合并产品）',institution:null,total:(body.match(/of\s+([\d,]+)\s+results for/i)||[])[1]||null,items};
  });
}
