/** 尚古汇典·典籍整理文献数据库：单页正文匹配结果的出处元数据。传入 CUA tab。 */
export async function gujidhSearch(tab, keyword) {
  if (typeof keyword !== 'string' || !keyword.trim() || keyword.length > 100) throw new Error('关键词须为 1–100 个字符');
  const query = keyword.trim();
  await tab.goto('https://www.gujidh.com/normal-search/' + encodeURIComponent(query) + '/content');
  await tab.playwright.locator('.items').filter({hasText:'结果出处：'}).first().waitFor({state:'visible', timeoutMs:20000});
  const results = await tab.playwright.evaluate(() => Array.from(document.querySelectorAll('.items')).filter(e => e.innerText.trim().startsWith('结果出处：')).map(e => {
    const rows = Array.from(e.parentElement.children).filter(x => x.classList.contains('items')).map(x => x.innerText.trim());
    const value = label => (rows.find(x => x.startsWith(label)) || '').slice(label.length).trim();
    return {source:value('结果出处：'), responsibility:value('责任者：'), publication:value('出版信息：')};
  }));
  return {database:'尚古汇典·典籍整理文献数据库', query, searchType:'正文匹配', institution:null, results, note:'仅返回当前页出处元数据；机构识别及全文权限未验证。'};
}
