/** Read a bounded bibliography from one manually initiated 月旦 result page. */
export function parseYuedanTables(tables, limit=5){
 if(!Array.isArray(tables)||!Number.isInteger(limit)||limit<1||limit>10)throw Error('无效表格或返回条数');
 const normalize=s=>String(s??'').replace(/\s+/g,' ').trim();
 let candidates=[];
 for(const table of tables){
  if(!Array.isArray(table))continue;
  for(let n=0;n<table.length;n++){
   let header=table[n].map(normalize);
   let idx={title:header.findIndex(x=>/^(篇名|題名|题名)$/.test(x)),journal:header.findIndex(x=>/^(刊名|期刊名)$/.test(x)),author:header.findIndex(x=>/^(作者|著者)$/.test(x)),date:header.findIndex(x=>/^(出版年月|出版日期|发表日期|發表日期)$/.test(x))};
   if(Object.values(idx).some(x=>x<0))continue;
   let items=[];
   for(const row of table.slice(n+1)){
    if(!Array.isArray(row))continue;let v=row.map(normalize);let title=v[idx.title];
    if(!title||/^(篇名|題名|题名)$/.test(title))continue;
    items.push({title,journal:v[idx.journal]||null,author:v[idx.author]||null,published:v[idx.date]||null});
   }
   if(items.length)candidates.push(items);
  }
 }
 if(candidates.length!==1)throw Error('未能唯一识别月旦题录表；页面可能发生变化或没有结果');
 return candidates[0].slice(0,limit);
}

export async function yuedanSearch(tab,keyword,submitSearch,limit=3){
 if(typeof keyword!=='string'||!keyword.trim()||keyword.length>100||typeof submitSearch!=='function'||!Number.isInteger(limit)||limit<1||limit>10)throw Error('需要关键词、当前页面的单次检索回调以及1–10条上限');
 await submitSearch();
 const data=await tab.playwright.evaluate(()=>{
  const u=new URL(location.href);let body=document.body?.innerText||'';
  return {host:u.hostname,path:u.pathname,total:body.match(/(?:檢索結果|检索结果)[：:]\s*共\s*([\d,]+)\s*筆/)?.[1]||null,
   tables:[...document.querySelectorAll('table')].map(t=>[...t.querySelectorAll('tr')].filter(r=>r.closest('table')===t).map(r=>[...r.children].filter(x=>/^(TD|TH)$/.test(x.tagName)).map(c=>(c.innerText||'').trim())))};
 });
 if(data.host!=='www.lawdata01.com.cn'||data.path!=='/anglekmc/lawkm')throw Error('不是月旦知识库结果页');
 if(!data.total)throw Error('未识别月旦检索总数；请确认结果已加载');
 const items=parseYuedanTables(data.tables,limit);
 return {source:'月旦知识库网页会话',query_submitted:keyword.trim(),total_display:data.total,items,note:'页面检索回调须由调用方提供并执行；只读首屏少量题录，无会话链接、全文或分页。结果页的关键词未独立验证，须由调用方确认当前结果对应本次查询；学校权限、自动提取及AI用途许可待核。'};
}
