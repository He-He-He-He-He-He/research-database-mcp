/** Read only currently visible public preview tables for one person. */
export async function inindexPersonPreview(tab,personId,limit=5){
 const id=String(personId);
 if(!/^[1-9]\d{0,9}$/.test(id)||!Number.isInteger(limit)||limit<1||limit>5)throw Error('需要人物编号和 1–5 条预览上限');
 const state=await tab.playwright.evaluate(()=>{
  const visible=e=>!!e&&e.getClientRects().length>0;
  const ids=['alias','addressList','kinship','provenance'];
  const sections=ids.map(id=>{const root=document.getElementById(id);if(!root||!visible(root))return null;
   const table=root.querySelector('table');if(!table||!visible(table))return null;
   const cells=row=>Array.from(row.querySelectorAll(':scope > th, :scope > td')).map(x=>x.innerText.trim());
   return {id,title:root.querySelector('.pt-title')?.innerText?.trim()||'',headers:Array.from(table.querySelectorAll('thead tr')).filter(visible).map(cells)[0]||[],rows:Array.from(table.querySelectorAll('tbody tr')).filter(visible).map(cells),notice:Array.from(root.querySelectorAll('button')).map(x=>x.innerText.trim()).filter(x=>/(付費機構|付费机构)/.test(x)).join(' ')};
  }).filter(Boolean);
  const u=new URL(location.href);return {host:u.hostname,path:u.pathname,personId:u.pathname.split('/')[3]||'',name:document.querySelector('h1')?.innerText?.trim()||'',translated:!!document.querySelector('#alias font, #addressList font, #kinship font, #provenance font'),sections};
 });
 if(state.host!=='www.inindex.com'||!state.path.startsWith('/biog/searchResult/')||state.personId!==id||!state.name)throw Error('人物详情页或编号不匹配');
 if(!state.sections.length||state.sections.some(x=>!x.headers.length))throw Error('当前预览表尚未加载或不可见');
 return {source:'引得历代人物传记资料库',id,name:state.name,translated_by_browser:state.translated,sections:state.sections.map(x=>({...x,rows:x.rows.slice(0,limit)})),note:'仅当前页面可见的别名、地点、亲属及出处预览；站方提示付费机构查看全部，不能把预览当作完整资料。浏览器翻译时为页面显示译文，未经校对；学校机构身份及全文权限未确认。'};
}
