/* 在已完成 CAB 基本检索的 Ovid 工作标签中跳转到指定记录。 */
export async function ovidCabPage(tab, keyword, start = 1) {
  if (typeof keyword !== 'string' || !keyword.trim() || keyword.length > 100) throw Error('关键词需为 1–100 字');
  if (!Number.isSafeInteger(start) || start < 1 || start > 1000000) throw Error('起始记录必须是 1–1000000 的整数');
  const q = keyword.trim();
  const initial = await tab.playwright.evaluate(() => ({resource: document.querySelector('#ovid-resources-link-block')?.innerText.trim(), info: document.querySelector('#searchaid-explain')?.innerText.trim()}));
  if (initial.resource !== 'CAB Abstracts + Full Text' || !initial.info?.includes(q)) throw Error('请先在 CAB 中完成相同关键词检索');
  await tab.playwright.locator('#startRecord').fill(String(start));
  await tab.playwright.locator('#toolbar-go-option input[type=submit]').first().click();
  for (let i = 0; i < 20; i++) {
    const d = await tab.playwright.evaluate(() => ({resource: document.querySelector('#ovid-resources-link-block')?.innerText.trim(), info: document.querySelector('#searchaid-explain')?.innerText.trim(), start: document.querySelector('#startRecord')?.value, rows: [...document.querySelectorAll('#titles-records .titles-row')].filter(e => e.getClientRects().length).map(e => ({number: Number(e.innerText.match(/^\s*(\d+)\./)?.[1]), title: e.querySelector('.article-title a')?.innerText.trim(), author: e.querySelector('.article-authors')?.innerText.trim(), source: e.querySelector('.article-source')?.innerText.trim(), type: e.querySelector('.article-pubtype')?.innerText.trim()})).filter(x => x.title)}));
    if (d.resource === 'CAB Abstracts + Full Text' && d.info?.includes(q) && d.start === String(start) && d.rows[0]?.number === start) return {source:'CAB Abstracts + Full Text via Ovid', query:q, start, items:d.rows, searchInfo:d.info, note:'当前结果页题录；检索默认含相关词，未读取摘要和全文。'};
    await new Promise(resolve => setTimeout(resolve, 500));
  }
  throw Error('未能确认指定记录位置，可能超出结果范围或页面未加载');
}
