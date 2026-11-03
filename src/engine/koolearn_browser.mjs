/** 新东方多媒体学习库，使用 CUA Tab 查询当前页课程目录。 */
export async function koolearnSearch(tab, keyword) {
  if (typeof keyword !== 'string' || !keyword.trim() || keyword.trim().length > 100) throw new Error('关键词须为 1–100 个字符');
  const query = keyword.trim();
  await tab.goto('https://library.koolearn.com/search?keywords=' + encodeURIComponent(query));
  await tab.playwright.locator('a[href^="/course/"] p').first().waitFor({state:'visible',timeoutMs:20000});
  const data = await tab.playwright.evaluate(() => ({
    institution: document.querySelector('img[alt="浙江大学"]') ? '浙江大学' : null,
    items: Array.from(document.querySelectorAll('a[href^="/course/"]')).filter(a => /^\/course\/\d+$/.test(a.getAttribute('href') || '')).map(a => ({title:a.querySelector('p')?.innerText.trim() || '',url:a.href})).filter(x=>x.title)
  }));
  return {source:'新东方多媒体学习库',query,page:1,...data,note:'当前页课程搜索结果；页面显示浙江大学标识，课程播放权限未验证。无结果或页面变化可能导致等待超时。'};
}
