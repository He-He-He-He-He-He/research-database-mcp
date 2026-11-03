/** 单页元数据；注入已绑定的 CUA 工作 tab。不读取正文，不保证机构订阅。 */
export async function oxfordReportsPage(tab,query) {
  if(typeof query!=='string'||!query.trim()) throw Error('关键词不能为空');
  const p=new URLSearchParams({sfam:'',q:query.trim(),prd:'ORIL',searchBtn:'Search'});
  await tab.goto('https://opil.ouplaw.com/search?'+p);
  await tab.playwright.locator('body').waitFor({state:'visible',timeoutMs:25000});
  return await tab.playwright.evaluate(()=>{
    const body=document.body.innerText;
    if(!body.includes('Search Results')) throw Error('未确认检索结果页');
    const items=[...document.querySelectorAll('.contentItem.standardResult')].filter(c=>c.getClientRects().length).map(c=>{
      const data=Object.fromEntries([...c.querySelectorAll('dl.metadata')].map(d=>[d.querySelector('dt')?.innerText.trim(),d.querySelector('dd')?.innerText.trim()]));
      return {title:c.querySelector('h2.itemTitle a')?.innerText.trim(),url:c.querySelector('h2.itemTitle a')?.href,date:data.Date||null,type:data['Content type']||null,product:data.Product||null,module:data.Module||null,jurisdiction:data.Jurisdiction||null,locked:c.classList.contains('locked')};
    }).filter(x=>x.title&&x.product?.includes('Oxford Reports on International Law'));
    return {source:'Oxford Reports on International Law',institution:null,total:(body.match(/of\s+([\d,]+)\s+results for/i)||[])[1]||null,items};
  });
}
export async function oedDictionaryPage(tab,query) {
  if(typeof query!=='string'||!query.trim()) throw Error('关键词不能为空');
  const p=new URLSearchParams({scope:'Entries',q:query.trim()});
  await tab.goto('https://www.oed.com/search/dictionary/?'+p);
  await tab.playwright.locator('body').waitFor({state:'visible',timeoutMs:25000});
  return await tab.playwright.evaluate(()=>{
    const body=document.body.innerText;
    if(!/results? for/i.test(body) && !/no results/i.test(body)) throw Error('未确认词典检索结果页');
    const items=[...document.querySelectorAll('.resultsSetItemBody')].filter(c=>c.getClientRects().length).map(c=>({title:c.querySelector('.resultTitle')?.innerText.trim(),url:c.querySelector('a.viewEntry')?.href,excerpt:c.querySelector('.snippet')?.innerText.trim()||null})).filter(x=>x.title&&x.url);
    return {source:'Oxford English Dictionary',institution:null,total:(body.match(/([\d,]+) results? for/i)||[])[1]||null,items};
  });
}
