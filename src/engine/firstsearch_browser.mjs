/** 读取当前 FirstSearch WorldCat 结果页面；不返回含会话标识的链接。 */
export async function firstSearchResults(tab) {
  const data = await tab.playwright.evaluate(() => {
    if (location.hostname !== 'firstsearch.oclc.org' || !location.pathname.endsWith('/FSQUERY')) throw new Error('请先在 FirstSearch 打开记录列表');
    const text = document.body.innerText;
    if (!text.includes('ZHEJIANG UNIV') || !text.includes('WorldCat') || !text.includes('找到的记录')) throw new Error('未识别浙江大学 WorldCat 结果页面');
    const summary = text.match(/WorldCat\s+检索项目：[\s\S]*?找到的记录：\s*([\d,]+)/);
    const items = Array.from(document.querySelectorAll('input[type=checkbox][name^="BookMark_"]')).map(el => {
      const row=el.closest('tr'); const title=row?.querySelector('a[href*="fetchtype=fullrecord"] b')?.textContent?.trim();
      const fields=row?.cells?.[2]?.innerText?.replace(/\s+/g,' ').trim() || '';
      return {title, fields};
    }).filter(x=>x.title);
    return {total: summary ? Number(summary[1].replace(/,/g,'')) : null, items};
  });
  if (!data.items.length || data.total === null) throw new Error('结果列表未能解析');
  return {source:'FirstSearch WorldCat', institution:'ZHEJIANG UNIV', ...data, note:'当前可见列表；排序与关键词匹配以原站为准；详情和全文未验证。'};
}
