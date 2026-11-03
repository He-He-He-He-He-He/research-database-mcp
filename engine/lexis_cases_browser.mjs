/** Read only a few case titles from the already displayed Lexis search result page. */
export async function lexisCasesPage(tab, keyword, options={}) {
 const query=typeof keyword==='string' ? keyword.trim() : '';
 const limit=options.limit ?? 3;
 if(!query || query.length>100 || !Number.isInteger(limit) || limit<1 || limit>5) throw Error('需要关键词及 1–5 条的 limit');
 const data=await tab.playwright.evaluate(({query,limit})=>{
  const u=new URL(location.href), displayed=u.searchParams.get('pdsearchterms');
  const heading=[...document.querySelectorAll('h2')].map(x=>x.textContent.trim()).find(x=>/^Cases\s*\(/.test(x));
  const rows=[...document.querySelectorAll('.casecardvalid')].slice(0,limit).map(x=>({title:x.querySelector('h2.doc-title a')?.textContent.trim(),metadata:[...x.querySelectorAll('.metadata > span')].map(y=>y.textContent.trim()).filter(Boolean)})).filter(x=>x.title);
  return {host:u.hostname,path:u.pathname,displayed,heading,rows};
 },{query,limit});
 if(data.host!=='advance.lexis.com'||data.path!=='/search/'||data.displayed!==query||!data.heading||!data.rows.length) throw Error('当前页面不是对应关键词的案例结果，或尚无结果；请在馆方会话中检索后再试');
 return {source:'Lexis馆方会话',query,case_count_display:data.heading,items:data.rows,scope:'当前 Cases 类别首屏少量标题和原始元数据；不读取摘要或全文',note:'仅核验当前页面；机构许可及第三方AI处理许可需要另行核对。'};
}
