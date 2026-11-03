/** Read the current first result page of one Kluwer Law Online search. */
export async function kluwerLawJournalSearch(tab, keyword, submitSearch, limit=5) {
 if (typeof keyword !== 'string' || !keyword.trim() || keyword.length > 150 || typeof submitSearch !== 'function' || !Number.isInteger(limit) || limit < 1 || limit > 10) throw Error('需要关键词、单次检索回调和 1–10 条上限');
 const query=keyword.trim();
 await submitSearch();
 const state=await tab.playwright.evaluate(()=>{
  const u=new URL(location.href);
  const normalized=s=>(s||'').replace(/\s+/g,' ').trim();
  const leaf=Array.from(document.querySelectorAll('*')).filter(e=>e.children.length===0).map(e=>normalized(e.textContent));
  const summary=leaf.find(x=>/^\d[\d,]* results? for /i.test(x))||'';
  const items=Array.from(document.querySelectorAll('a[href^="/JournalArticle/"]')).map(a=>({title:normalized(a.textContent), citation:normalized(a.parentElement?.textContent).replace(normalized(a.textContent),'').trim(), url:new URL(a.getAttribute('href'),location.origin).href})).filter(x=>x.title);
  return {host:u.hostname,path:u.pathname,query:u.searchParams.get('searchText')||'',summary,items};
 });
 if(state.host!=='kluwerlawonline.com'||!state.path.startsWith('/SearchContent/')||state.query!==query)throw Error('结果页面或搜索词不匹配');
 const m=state.summary.match(/^([\d,]+) results? for (.+)$/i);
 if(!m||m[2]!==query)throw Error('检索结果尚未加载或无法核对总数');
 const total=Number(m[1].replaceAll(',',''));
 if(total>0&&!state.items.length)throw Error('当前页未显示可核对的期刊题录');
 return {source:'Kluwer Law Online',query,total_all_content:total,items:state.items.slice(0,limit),note:'总数包含期刊、百科与手册；只返回当前首屏可见期刊题录。此为公开搜索页，未核验浙江大学机构身份及全文权限。'};
}
