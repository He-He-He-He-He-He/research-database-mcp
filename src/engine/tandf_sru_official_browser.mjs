/** Taylor & Francis Online official SRU, via a dedicated browser tab. */
export async function tandfSruSearch(tab, keyword, page = 1, pageSize = 5) {
  if (typeof keyword !== 'string' || !keyword.trim() || keyword.length > 100 || /["\\\r\n]/.test(keyword)) throw Error('keyword must be 1–100 characters without quotes or backslashes');
  if (!Number.isInteger(page) || page < 1 || page > 100 || !Number.isInteger(pageSize) || pageSize < 1 || pageSize > 20) throw Error('page must be 1–100 and pageSize 1–20');
  const query = `cql.anywhere="${keyword.trim()}"`;
  const params = new URLSearchParams({query, maximumRecords: String(pageSize), startRecord: String((page - 1) * pageSize + 1)});
  await tab.goto('https://www.tandfonline.com/action/sru?' + params.toString());
  const data = await tab.playwright.evaluate(() => {
    const u = new URL(location.href);
    const txt = (root, sel) => root.querySelector(sel)?.textContent?.trim() || null;
    return {host:u.hostname, path:u.pathname, query:u.searchParams.get('query'), start:u.searchParams.get('startRecord'), contentType:document.contentType,
      total:txt(document,'numberOfRecords'), records:[...document.querySelectorAll('record')].map(r=>({title:txt(r,'title'), doi:txt(r,'identifier'), authors:[...r.querySelectorAll('contributor')].map(e=>e.textContent.trim()), publication:txt(r,'isPartOf'), date:txt(r,'date'), url:txt(r,'url'), position:txt(r,'recordPosition')}))};
  });
  if (data.host !== 'www.tandfonline.com' || data.path !== '/action/sru' || data.query !== query || data.start !== String((page-1)*pageSize+1) || data.contentType !== 'application/xml' || !/^\d+$/.test(data.total || '') || data.records.length > pageSize) throw Error('Taylor & Francis SRU response not recognized; normal browser verification may be required');
  return {source:'Taylor & Francis Online official SRU', keyword:keyword.trim(), page, pageSize, total:Number(data.total), records:data.records, note:'出版社联合检索接口；全平台题录不证明浙大订购范围、全文权限或 AI 用途授权。'};
}
