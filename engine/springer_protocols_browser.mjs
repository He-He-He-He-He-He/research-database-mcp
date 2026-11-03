/** 只读 Springer Nature Experiments 当前结果页中标示 Springer Protocols 的题录。 */
export async function springerProtocolsCurrent(tab, query) {
 if(typeof query!=='string'||!query.trim()||query.length>200) throw Error('关键词须为1–200字');
 const q=query.trim();
 const d=await tab.playwright.evaluate(()=>({url:location.href,summary:document.querySelector('#search_summary')?.innerText||'',items:[...document.querySelectorAll('li.SN_search-Results__searched_content')].filter(x=>x.getClientRects().length).map(x=>({title:x.querySelector('h3 a.title')?.innerText.trim()||'',url:x.querySelector('h3 a.title')?.href||'',label:x.innerText.slice(0,300)})).filter(x=>x.title&&x.url&&/Springer Protocols/.test(x.label)).map(({title,url})=>({title,url}))}));
 const p=new URL(d.url);if(p.hostname!=='experiments.springernature.com'||p.pathname!=='/search'||p.searchParams.get('term')!==q||!d.items.length)throw Error('未确认关键词或 Springer Protocols 当前页题录');
 return {source:'Springer Protocols',query:q,...d,note:'仅当前页逐项标为 Springer Protocols 的题录；总数是页面查询总数，不一定限于该来源。未验证机构身份和全文。'};
}
