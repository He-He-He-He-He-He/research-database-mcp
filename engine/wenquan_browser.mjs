/** 文泉学堂浙大站：使用已绑定的 CUA 浏览器 Tab 读取单页检索题录。 */
export async function wenquanSearch(tab, keyword) {
  if (typeof keyword !== 'string' || !keyword.trim() || keyword.trim().length > 100) throw new Error('关键词须为 1–100 个字符');
  const query = keyword.trim();
  await tab.goto('https://lib-zju.wqxuetang.com/search?kw=' + encodeURIComponent(query));
  await tab.playwright.locator('.sort_btn_box').first().waitFor({state:'visible', timeoutMs:20000});
  const data = await tab.playwright.evaluate(() => ({
    institution: document.querySelector('.school')?.innerText.trim() || null,
    total: (() => { const n = document.querySelector('.sort_btn_box .red')?.innerText.trim(); return n && /^\d+$/.test(n) ? Number(n) : null; })(),
    items: Array.from(document.querySelectorAll('.myss')).map(e => ({
      title: e.querySelector('h3')?.innerText.trim() || '',
      metadata: e.querySelector('.item-author')?.innerText.trim() || '',
      type: e.querySelector('.in-r-tip')?.innerText.trim() || '',
      keywords: Array.from(e.querySelectorAll('.item-kw li')).map(x => x.innerText.trim()).filter(Boolean)
    })).filter(x => x.title)
  }));
  return {source:'文泉学堂', query, page:1, ...data, note:'当前页题录；页面显示机构名称，具体内容访问权限未验证。无结果或页面变化可能导致等待超时。'};
}
