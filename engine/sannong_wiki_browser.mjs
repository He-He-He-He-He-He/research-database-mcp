/** 智汇三农农业百科首屏题录；传入 CUA 工作标签页。 */
export async function sannongWikiSearch(tab,keyword) {
 if(typeof keyword!=='string'||!keyword.trim()||keyword.length>100) throw Error('关键词须为 1–100 个字符');
 const query=keyword.trim();
 await tab.goto('https://www.pwsannong.com/booklib/search?w='+encodeURIComponent(encodeURIComponent(query))+'&SiteID=123&type=Wiki&sublibid=');
 await tab.playwright.locator('#resultList .abstract-item h4 a').first().waitFor({state:'visible',timeoutMs:20000});
 const items=await tab.playwright.evaluate(()=>Array.from(document.querySelectorAll('#resultList .abstract-item')).map(e=>{
  const a=e.querySelector('h4 a'); const lines=(e.querySelector('.book-attribute')?.innerText||'').split('\n').map(x=>x.trim()).filter(Boolean);
  const field=(key)=>{const i=lines.indexOf(key);return i<0?'':lines[i+1]||''};
  return {title:a?.innerText.trim()||'',url:a?.href||'',date:field('发布日期：'),author:field('作者：')};
 }).filter(x=>x.title));
 return {source:'智汇三农农业百科',query,page:1,institution:null,items,note:'当前页百科题录；未见机构标识，正文权限未验证，空结果可能超时。'};
}
