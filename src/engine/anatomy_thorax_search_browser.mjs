/** Read one visible, user-authorized anatomy search from the current institution browser session. */
export async function anatomyThoraxSearch(homeTab, productTab, keyword, submitAndExpand, limit=5){
 if(typeof keyword!=='string'||!keyword.trim()||keyword.length>100||typeof submitAndExpand!=='function'||!Number.isInteger(limit)||limit<1||limit>10)throw Error('需要关键词、搜索回调和 1–10 条上限');
 const query=keyword.trim();
 const home=await homeTab.playwright.evaluate(()=>({host:location.hostname, text:document.body?.innerText||''}));
 if(home.host!=='www.anatomy.tv'||!/(浙江大学|Zhejiang University)/i.test(home.text))throw Error('主页未识别浙江大学机构会话');
 await submitAndExpand();
 const state=await productTab.playwright.evaluate(()=>{
  const input=document.querySelector('#input-search');
  const header=document.querySelector('.texts-search-block');
  const block=document.querySelector('#texts-search-block-parent');
  const nodes=block?Array.from(block.querySelectorAll('.index-icon')):[];
  const empty=document.querySelector('#search-results .search-list.empty');
  return {host:location.hostname,hash:location.hash,query:input?.value||'',heading:header?.textContent?.trim()||'',expanded:!!block&&!!block.parentElement?.classList.contains('expanded'),
   names:nodes.map(x=>x.getAttribute('data-title')).filter(Boolean),noResults:!header&&!block&&empty?.textContent?.trim()==='No results'};
 });
 if(state.host!=='www.anatomy.tv'||!state.hash.startsWith('#/product/har_thorax_2014/')||state.query.trim()!==query)throw Error('图谱或搜索词与当前页面不匹配');
 const m=state.heading.match(/^In Anatomical structures\s*\((\d+)\)$/i);
 if(!state.noResults&&(!m||!state.expanded))throw Error('请在图谱中展开 Anatomical structures 搜索结果');
 const total=state.noResults?0:Number(m[1]);
 if(total>0&&!state.names.length)throw Error('搜索结果尚未加载');
 return {source:'Anatomy.tv Primal 3D Atlas of Thorax and Abdomen',institution:'浙江大学（主页显示）',keyword:query,total,
  items:state.names.slice(0,limit).map(name=>({name})),loaded_results:state.names.length,
  note:'仅当前胸腹 3D 图谱中已经加载的解剖结构名称；列表可能懒加载，不代表全库或其他模块均可访问。'};
}
