/** Ulrichsweb 期刊目录，使用已有的机构浏览器会话。 */
export async function ulrichsSearch(tab, query) {
 if(typeof query!=='string'||!query.trim()||query.length>200) throw Error('关键词不能为空且不得超过 200 字符');
 await tab.goto('https://libdb.zju.edu.cn/s/lib/libtb/turning/1030');
 const input=tab.playwright.locator('input#query').first();
 await input.waitFor({state:'visible',timeoutMs:25000});
 await input.fill(query.trim());
 await input.press('Enter');
 let ready=false;
 for(let attempt=0;attempt<3&&!ready;attempt++) {
  try { await tab.playwright.locator('#list tr.jqgrow a.titleDetailsLink').first().waitFor({state:'visible',timeoutMs:10000}); ready=true; }
  catch(e) { if(attempt===2) throw e; }
 }
 return await tab.playwright.evaluate(() => {
  const rows=[...document.querySelectorAll('#list tr.jqgrow')];
  const get=(row,name)=>{const e=row.querySelector(`[aria-labelledby="jqgh_${name}"]`);return e?.innerText.trim()||null};
  const items=rows.map(row=>{const a=row.querySelector('a.titleDetailsLink');return {title:a?.innerText.trim()||null,url:a?.href||null,publisher:get(row,'Publisher'),issn:get(row,'ISSN'),country:get(row,'Country'),status:get(row,'Status'),serial_type:get(row,'SerialType'),format:get(row,'Format')};}).filter(x=>x.title&&x.url);
  return {source:'Ulrichsweb',institution:document.body.innerText.includes('Zhejiang University Library')?'Zhejiang University Library':null,display_count:document.querySelector('#showResults')?.innerText.trim()||null,items,note:'当前页期刊目录，非文章全文；字段和刊物状态以原站为准。'};
 });
}
