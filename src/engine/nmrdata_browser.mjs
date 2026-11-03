/** 微谱数据化合物名称检索，读取当前页题录，传入已绑定 CUA Tab。 */
export async function nmrdataSearch(tab, keyword) {
  if (typeof keyword !== 'string' || !keyword.trim() || keyword.trim().length > 100) throw new Error('关键词须为 1–100 个字符');
  const query=keyword.trim();
  await tab.goto('https://www.nmrdata.com/ChemicalSearch.aspx');
  await tab.playwright.locator('#txtContent').fill(query);
  await tab.playwright.locator('#btnSearch').click();
  await tab.playwright.locator('#lblCount').waitFor({state:'visible',timeoutMs:20000});
  const data=await tab.playwright.evaluate(()=>({institution:document.body.innerText.includes('当前单位:浙江大学')?'浙江大学':null, countText:document.querySelector('#lblCount')?.innerText.trim()||'',items:Array.from(document.querySelectorAll('#dtlDisplay blockquote')).map(e=>{const p=Array.from(e.querySelectorAll('p'));return {compound:p[0]?.innerText.trim().replace(/\s+/g,' ')||'',source:p[1]?.innerText.trim().replace(/\s+/g,' ')||'',title:p[2]?.innerText.trim()||'',authors:p[3]?.innerText.trim()||''};}).filter(x=>x.title)}));
  return {source:'微谱数据',query,page:1,...data,note:'化合物名称搜索当前页题录；结构和谱图未读取，页面显示机构名。'};
}
