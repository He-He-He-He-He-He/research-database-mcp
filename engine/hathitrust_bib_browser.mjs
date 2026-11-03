/** HathiTrust's official, small-scale single-identifier Bibliographic API. */
export async function hathiBib(tab, type, id) {
 const valid = {oclc:/^\d{1,20}$/, isbn:/^(?:\d{10}|\d{9}[Xx]|\d{13})$/, issn:/^\d{7}[\dXx]$/, recordnumber:/^\d{9}$/, htid:/^[A-Za-z0-9._-]{1,100}$/};
 if (!Object.hasOwn(valid,type) || typeof id !== 'string') throw Error('invalid identifier');
 // ISBN and ISSN are conventionally written with spaces or hyphens.
 // Strip separators only after checking the input's complete character set.
 if (type === 'isbn' || type === 'issn') {
  if (!/^[0-9Xx -]+$/.test(id)) throw Error('invalid identifier');
  id=id.replace(/[ -]/g,'');
 }
 if (!valid[type].test(id)) throw Error('invalid identifier');
 const url = `https://catalog.hathitrust.org/api/volumes/brief/${type}/${encodeURIComponent(id)}.json`;
 await tab.goto(url);
 const d = await tab.playwright.evaluate(() => ({host:location.hostname,path:location.pathname,body:document.body.innerText}));
 if (d.host !== 'catalog.hathitrust.org' || d.path !== new URL(url).pathname) throw Error('unexpected API location');
 let data; try { data=JSON.parse(d.body); } catch { throw Error('HathiTrust API response is unavailable or not JSON'); }
 if (!data || typeof data.records !== 'object' || !Array.isArray(data.items)) throw Error('unexpected HathiTrust response');
 return {source:'HathiTrust Bibliographic API',source_info:'https://www.hathitrust.org/member-libraries/resources-for-librarians/data-resources/bibliographic-api/',identifier_type:type,identifier:id,records:data.records,items:data.items,note:'标识符查找，不支持关键词检索；卷册权限字段中的 usRightsString 只针对美国用户，不表示浙大或当前位置可读全文。仅小量调用；元数据可能受第三方限制。'};
}
