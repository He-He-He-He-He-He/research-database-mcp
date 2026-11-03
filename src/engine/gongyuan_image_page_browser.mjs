/** Read one normally navigated results page from the ZJU campus image library. */
export async function gongyuanImagePage(tab, keyword, {page, submitSearch, limit = 3} = {}) {
  if (typeof keyword !== 'string' || !keyword.trim() || keyword.length > 100 || !Number.isInteger(page) || page < 1 || !Number.isInteger(limit) || limit < 1 || limit > 10 || typeof submitSearch !== 'function') throw Error('需要关键词、页码、单次页面操作回调及 1–10 条上限');
  await submitSearch();
  let d;
  for (let n = 0; n < 30; n++) {
    d = await tab.playwright.evaluate(() => ({host:location.hostname,path:location.pathname,search:location.search,title:document.title,text:document.body.innerText,rows:[...document.querySelectorAll('a[href*="image.php?type=detail&id="]')].map(a=>({href:a.getAttribute('href'),caption:a.closest('table')?.parentElement?.closest('table')?.querySelector('font.f')?.innerText||''}))}));
    const m = d.search.match(/(?:^|[?&])page=(\d+)(?:&|$)/);
    const p = m ? Number(m[1]) : 1;
    if (d.host === '10.15.61.245' && d.path === '/search.php' && d.title.includes('浙江大学') && p === page && d.text.includes('含有"'+keyword.trim()+'"的结果') && d.rows.length) break;
    await new Promise(resolve => setTimeout(resolve, 250));
  }
  const m = d?.search.match(/(?:^|[?&])page=(\d+)(?:&|$)/);
  if (d?.host !== '10.15.61.245' || d.path !== '/search.php' || !d.title.includes('浙江大学') || (m ? Number(m[1]) : 1) !== page || !d.text.includes('含有"'+keyword.trim()+'"的结果')) throw Error('机构、检索词或页面不匹配');
  const count = d.text.match(/共\s*(\d+)\s*项\s*(\d+)\s*页/);
  if (!count || !d.rows.length || page > Number(count[2])) throw Error('结果或页码不可验证');
  const items = d.rows.slice(0,limit).map(x => {const id=x.href?.match(/^image\.php\?type=detail&id=(\d+)$/);if (!id || !x.caption.trim()) throw Error('图片编号或说明缺失');return {id:id[1],caption_snippet:x.caption.trim()};});
  return {source:'公元集成教学图片数据库（浙大会话）',query:keyword.trim(),page,total:Number(count[1]),pages:Number(count[2]),items,note:'只读取普通检索当前页图片编号和页面截断说明，不复制图片；使用范围以学校许可为准。'};
}
