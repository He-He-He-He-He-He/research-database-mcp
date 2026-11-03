/* 引得历代人物：通过真实网页进行单次姓名检索，读取首屏结果。 */
export async function inindexSearch(tab, keyword) {
  if (typeof keyword !== 'string' || !keyword.trim() || keyword.length > 100) throw Error('姓名需为 1–100 字');
  await tab.goto('https://www.inindex.com/biog');
  const field = tab.playwright.getByPlaceholder('請輸入關鍵詞搜索');
  await field.fill(keyword.trim());
  await tab.playwright.getByRole('button', {name: '去發現'}).click();
  try { await tab.playwright.locator('table tbody tr a').first().waitFor({state:'visible', timeoutMs:15000}); }
  catch (_) { throw Error('未读取到人物结果；可能无匹配、需要登录或页面变化，请在网页检查。'); }
  const items = await tab.playwright.evaluate(() => [...document.querySelectorAll('table tbody tr')].map(row => {
    const c = [...row.querySelectorAll('td')].map(e => e.innerText.trim());
    const a = row.querySelector('a');
    return a ? {id:c[1], name:c[2], aliases:c[3], gender:c[4], period:c[5], place:c[6], birth:c[7], death:c[8], estimatedBirth:c[9], url:a.href} : null;
  }).filter(Boolean));
  return {source:'引得历代人物', query:keyword.trim(), page:1, institution:null, items, note:'机构身份未见显示；仅返回网页首屏，别名不一定能作为人名匹配。'};
}
