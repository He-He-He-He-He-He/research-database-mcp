/** 京东读书专业版，使用 CUA Tab 读取首屏题录。 */
export async function jdReadSearch(tab, keyword) {
  if (typeof keyword !== 'string' || !keyword.trim() || keyword.trim().length > 100) throw new Error('关键词须为 1–100 个字符');
  const query=keyword.trim();
  await tab.goto('https://m-tob.jd.com/search_dosearch?serch='+encodeURIComponent(query));
  await tab.playwright.locator('.book-card-h .book-name').first().waitFor({state:'visible',timeoutMs:20000});
  const items=await tab.playwright.evaluate(()=>Array.from(document.querySelectorAll('.book-card-h')).map(e=>({title:e.querySelector('.book-name')?.innerText.trim() || '',author:e.querySelector('.book-author')?.innerText.trim() || ''})).filter(x=>x.title));
  return {source:'京东读书专业版',query,items,institution:null,note:'当前加载的题录；页面未显示机构身份，阅读权限未验证。无结果或页面变化可能导致等待超时。'};
}
