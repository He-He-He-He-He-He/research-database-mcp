// Decode only a small fixed set of named entities once, without interpreting HTML.
export function decodeSruTitle(value) {
  if (value === null) return null;
  const entities = {amp: '&', lt: '<', gt: '>', quot: '"', apos: "'"};
  return value.replace(/&(amp|lt|gt|quot|apos);/g, (_, name) => entities[name]);
}

/** Emerald official SRU, via a dedicated browser tab. */
export async function emeraldSruSearch(tab, keyword, page = 1, pageSize = 5) {
  if (typeof keyword !== 'string' || !keyword.trim() || keyword.length > 100 || /["\\\r\n]/.test(keyword)) throw Error('keyword must be 1–100 characters without quotes or backslashes');
  if (!Number.isInteger(page) || page < 1 || page > 100 || !Number.isInteger(pageSize) || pageSize < 1 || pageSize > 20) throw Error('page must be 1–100 and pageSize 1–20');
  const query = `cql.anywhere="${keyword.trim()}"`;
  const params = new URLSearchParams({operation:'searchRetrieve',version:'2.0',query,maximumRecords:String(pageSize),startRecord:String((page-1)*pageSize+1)});
  await tab.goto('https://www.emerald.com/sru?' + params.toString());
  const d = await tab.playwright.evaluate(() => {
    const u=new URL(location.href), text=(root,sel)=>root.querySelector(sel)?.textContent?.trim()||null;
    return {host:u.hostname,path:u.pathname,query:u.searchParams.get('query'),start:u.searchParams.get('startRecord'),contentType:document.contentType,total:text(document,'numberOfRecords'),records:[...document.querySelectorAll('record')].map(r=>({title:text(r,'title'),doi:text(r,'identifier'),authors:[...r.querySelectorAll('contributor')].map(e=>e.textContent.trim()),publication:text(r,'isPartOf'),date:text(r,'date'),resource_type:text(r,'type'),rights_raw:text(r,'rights'),url:text(r,'url'),position:text(r,'recordPosition')}))};
  });
  if(d.host!=='www.emerald.com'||d.path!=='/sru'||d.query!==query||d.start!==String((page-1)*pageSize+1)||d.contentType!=='application/xml'||!/^\d+$/.test(d.total||'')||d.records.length>pageSize)throw Error('Emerald SRU response not recognized; normal browser verification may be required');
  const records = d.records.map(record => ({...record, title_raw: record.title, title: decodeSruTitle(record.title)}));
  return {source:'Emerald official SRU',keyword:keyword.trim(),page,pageSize,total:Number(d.total),records,note:'出版社全平台题录；不证明浙大订购范围、全文或 AI 用途授权。'};
}
