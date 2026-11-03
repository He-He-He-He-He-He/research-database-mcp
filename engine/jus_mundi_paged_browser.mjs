/* Jus Mundi 公开可见检索页；不推断学校订购或全文权限。 */
export async function jusMundiPaged(tab, query, page = 1) {
  if (typeof query !== 'string' || !query.trim() || query.length > 200) throw Error('关键词需为 1–200 字');
  if (!Number.isSafeInteger(page) || page < 1 || page > 10000) throw Error('页数需为 1–10000 的整数');
  const q = query.trim(), p = new URLSearchParams({lang:'en', query:q, sort:'relevance', page:String(page)});
  await tab.goto('https://jusmundi.com/en/search?' + p);
  for (let i=0; i<25; i++) {
    const r = await tab.playwright.evaluate(({q,page}) => {
      const m = document.body.innerText.match(/Showing\s+([\d,]+)\s+to\s+([\d,]+)\s+out of\s+([\d,]+)\s+results/i);
      const links=[...document.querySelectorAll('a[data-tracking="click_search_result"]')].filter(a=>a.getClientRects().length && a.innerText.trim() && a.hasAttribute('href'));
      const nested=links[0] && new URL(links[0].href).searchParams.get('su');
      if (!m || !nested) return null;
      const source=new URL(nested,location.origin);
      if (source.searchParams.get('query') !== q || Number(source.searchParams.get('page') || 1) !== page) return null;
      return {first:Number(m[1].replaceAll(',','')),last:Number(m[2].replaceAll(',','')),total:Number(m[3].replaceAll(',','')),items:links.map(a=>({title:a.innerText.trim(),url:a.href}))};
    },{q,page});
    if (r?.items.length && r.first === (page-1)*10+1) return {source:'Jus Mundi',query:q,page,...r,note:'当前页面可见题录，不代表机构认证或全文权限。'};
    await new Promise(resolve=>setTimeout(resolve,1000));
  }
  throw Error('未能确认指定结果页，可能无结果或超出范围');
}
