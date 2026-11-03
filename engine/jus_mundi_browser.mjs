/** Jus Mundi 公共可见搜索结果；不推断机构身份或全文权限。 */
export async function jusMundiPage(tab,query) {
  if(typeof query!=='string'||!query.trim()) throw Error('关键词不能为空');
  query=query.trim();
  const p=new URLSearchParams({lang:'en',query,sort:'relevance'});
  await tab.goto('https://jusmundi.com/en/search?'+p);
  for(let attempt=0;attempt<20;attempt++) {
    const result=await tab.playwright.evaluate((expected)=>{
      const body=document.body.innerText;
      const total=(body.match(/Showing\s+1\s+to\s+\d+\s+out of\s+([\d,]+)\s+results/i)||[])[1];
      const links=[...document.querySelectorAll('a[data-tracking="click_search_result"]')].filter(a=>a.getClientRects().length && a.innerText.trim() && a.hasAttribute('href'));
      const nested=links[0]&&new URL(links[0].href).searchParams.get('su');
      if(!total || !nested || new URL(nested,location.origin).searchParams.get('query')!==expected) return null;
      return {source:'Jus Mundi',institution:null,total,items:links.map(a=>({title:a.innerText.trim(),url:a.href}))};
    },query);
    if(result?.items?.length) return result;
    await new Promise(resolve=>setTimeout(resolve,1000));
  }
  throw Error('结果未加载或没有可确认的结果');
}
