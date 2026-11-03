/** 中国社会科学文库普通结果页题录，依赖当前浏览器会话。 */
export async function sklibSearch(tab, query) {
 if(typeof query!=='string'||query!==query.trim()||!query||query.length>100)throw Error('关键词需为 1–100 字');
 const u=new URL('https://www.sklib.cn/booklib/search');
 for(const [k,v] of Object.entries({SiteID:'122',resType:'',q:encodeURIComponent(query),field:'all',preciseSearch:'N'}))u.searchParams.set(k,v);
 await tab.goto(u.href);
 for(let i=0;i<20;i++){
  const d=await tab.playwright.evaluate(()=>{const u=new URL(location.href),text=document.body.innerText,m=text.match(/([\d,]+)\s*个检索结果/);const items=[...document.querySelectorAll('#img-data-list .list-item')].map(e=>({title:e.querySelector('.list-item__title')?.innerText.trim()||null,type:e.querySelector('h4 .tab.pc')?.innerText.trim()||null})).filter(x=>x.title);return {host:u.hostname,path:u.pathname,q:document.querySelector('#queryText')?.value,page:Number(document.querySelector('#pageBar .curr')?.innerText),total:m?Number(m[1].replaceAll(',','')):null,institution:text.includes('浙江大学'),items};});
  if(d.host==='www.sklib.cn'&&d.path==='/booklib/search'&&d.q===query&&d.page===1&&d.total!==null&&d.items.length){
   // 机构名称可能晚于题录异步加载；未见标识仅表示未知，并非未授权。
   if(!d.institution){await new Promise(resolve=>setTimeout(resolve,1000));d.institution=await tab.playwright.evaluate(()=>document.body.innerText.includes('浙江大学'));}
   return {source:'中国社会科学文库',query,total:d.total,institutionShown:d.institution?true:null,items:d.items,note:'普通模糊检索结果页标题与资源类型；不含摘要、详情和全文。机构标识不证明全文权限。'};
  }
  await new Promise(resolve=>setTimeout(resolve,500));
 }
 throw Error('未确认社科文库结果；可能无结果、会话失效或要求安全验证');
}
