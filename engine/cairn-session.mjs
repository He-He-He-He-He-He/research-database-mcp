/** Cairn.info 人文社科题录，只读单页网页检索，传入 CUA 工作标签。 */
export async function searchCairn(tab,keyword){
 if(typeof keyword!=='string'||!keyword.trim()||keyword.length>100||/[\r\n]/.test(keyword))throw new Error('关键词需为1–100字单行文本');
 const query=keyword.trim();
 const initial=await tab.getAXState({emit:false,disableDiffing:true});
 if(!initial.includes('shs.cairn.info/'))throw new Error('请先打开 Cairn.info 工作标签');
 await tab.goto('https://shs.cairn.info/recherche?lang=fr&term='+encodeURIComponent(query));
 const result=await tab.playwright.evaluate(()=>{
  const h=document.querySelector('main h1')?.innerText||'';
  const match=document.querySelector('main')?.innerText.match(/([\d\s\u202f]+)\s+résultats?/i);
  const items=[...document.querySelectorAll('main h3')].map(x=>{
   const card=x.closest('div.shadow-halo-sm');if(!card)return null;
   const link=card.querySelector('a[aria-label][href]');
   return {title:x.innerText.trim(),url:link?.href||null,metadata:x.parentElement.innerText.trim()};
  }).filter(x=>x?.title&&x.url);
  return {heading:h,count:match?Number(match[1].replace(/\s|\u202f/g,'')):null,items};
 });
 if(!result.heading.includes(query)||result.count===null)throw new Error('未确认检索结果，可能页面改版或需要登录');
 return {query,source:'Cairn.info Sciences Humaines et Sociales',total:result.count,items:result.items,note:'首屏公开题录；机构身份与全文权限尚未验证。'};
}
