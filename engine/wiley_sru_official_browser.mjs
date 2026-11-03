// Decode only a small fixed set of named entities once, without interpreting HTML.
export function decodeSruTitle(value) {
  if (value === null) return null;
  const entities = {amp: '&', lt: '<', gt: '>', quot: '"', apos: "'"};
  return value.replace(/&(amp|lt|gt|quot|apos);/g, (_, name) => entities[name]);
}

/** Wiley's public Federated Search SRU through a dedicated browser tab. */
export async function wileySruSearch(tab, keyword, page = 1, pageSize = 5) {
  if (typeof keyword !== 'string' || !keyword.trim() || keyword.length > 100 || /["\\\r\n]/.test(keyword)) throw Error('keyword must be 1–100 characters without quotes or backslashes');
  if (!Number.isInteger(page) || page < 1 || page > 100 || !Number.isInteger(pageSize) || pageSize < 1 || pageSize > 20) throw Error('page must be 1–100 and pageSize 1–20');
  const query = `cql.anywhere="${keyword.trim()}"`;
  const params = new URLSearchParams({query, maximumRecords: String(pageSize), startRecord: String((page - 1) * pageSize + 1)});
  await tab.goto('https://onlinelibrary.wiley.com/action/sru?' + params.toString());
  const data = await tab.playwright.evaluate(() => {
    const u = new URL(location.href);
    const txt = (root, sel) => root.querySelector(sel)?.textContent?.trim() || null;
    return {host:u.hostname, path:u.pathname, query:u.searchParams.get('query'), start:u.searchParams.get('startRecord'), contentType:document.contentType,
      total:txt(document,'numberOfRecords'), records:[...document.querySelectorAll('record')].map(r=>({title:txt(r,'title'), doi:txt(r,'identifier'), authors:[...r.querySelectorAll('contributor')].map(e=>e.textContent.trim()), publication:txt(r,'isPartOf'), date:txt(r,'date'), url:txt(r,'url'), position:txt(r,'recordPosition')}))};
  });
  if (data.host !== 'onlinelibrary.wiley.com' || data.path !== '/action/sru' || data.query !== query || data.start !== String((page-1)*pageSize+1) || data.contentType !== 'application/xml' || !/^\d+$/.test(data.total || '') || data.records.length > pageSize) throw Error('Wiley SRU response not recognized; it may require normal browser verification');
  const records = data.records.map(record => ({...record, title_raw: record.title, title: decodeSruTitle(record.title),
    identifier_raw: record.doi,
    doi: record.doi && !/\u004010\.1111\/\(issn\)/i.test(record.doi) ? record.doi : null,
    identifier_note: record.doi && /\u004010\.1111\/\(issn\)/i.test(record.doi) ? 'Contains a Wiley ISSN collection suffix; verify the original identifier independently.' : null}));
  return {source:'Wiley Online Library Federated Search SRU', keyword:keyword.trim(), page, pageSize, total:Number(data.total), records, note:'官方机构联合检索 API；返回 Wiley 全平台元数据，不证明浙江大学订购范围、全文权限或 AI 用途授权。'};
}
