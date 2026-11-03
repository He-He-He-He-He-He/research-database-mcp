/** 识典古籍书籍检索。传入已由 CUA 创建的浏览器标签页；只返回当前页面元数据。 */
export async function shidianSearch(tab, keyword) {
  if (typeof keyword !== 'string' || !keyword.trim() || keyword.length > 100) throw new Error('关键词须为 1–100 个字符');
  const query = keyword.trim();
  await tab.goto('https://www.shidianguji.com/search/' + encodeURIComponent(query) + '?page_from=home_page');
  await tab.playwright.locator('#semiTabPanelparagraph a[href*="/chapter/"]').first().waitFor({state:'visible',timeoutMs:20000});
  await tab.playwright.getByRole('tab',{name:'搜书籍'}).click();
  await tab.playwright.getByRole('button',{name:'搜索',exact:true}).click();
  await tab.playwright.locator('#semiTabPanelbook a[href^="/book/"]').first().waitFor({state:'visible',timeoutMs:20000});
  const results = await tab.playwright.evaluate(() => Array.from(document.querySelectorAll('#semiTabPanelbook a[href^="/book/"]')).map(e => {
    const lines = e.innerText.split('\n').map(s=>s.trim()).filter(Boolean);
    const title = lines.shift() || '';
    const labels=[]; while (lines.length && ['精校','粗校','译文'].includes(lines[0])) labels.push(lines.shift());
    return {title, labels, details:lines[0] || '', url:new URL(e.getAttribute('href'),location.origin).href};
  }));
  return {database:'识典古籍',query,results,institution:null,note:'仅书籍检索当前页；机构身份与全文权限未验证。无结果或加载失败可能超时。'};
}
