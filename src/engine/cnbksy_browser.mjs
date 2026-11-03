/* 全国报刊索引：正常网页会话中的单次普通检索，返回首屏题录。 */
export async function cnbksySearch(tab, keyword) {
  if (typeof keyword !== 'string' || !keyword.trim() || keyword.length > 100) throw Error('关键词需为 1–100 字');
  await tab.goto('https://www.cnbksy.com/v2/');
  await tab.playwright.locator('#imgSearch').fill(keyword.trim());
  await tab.playwright.getByRole('button',{name:'搜索',exact:true}).click();
  try { await tab.playwright.locator('table tbody tr[data-row-key] .titleBox').first().waitFor({state:'visible',timeoutMs:20000}); }
  catch (_) { throw Error('未读取到题录；可能无结果、需要登录、验证或页面变化，请检查网页。'); }
  const result=await tab.playwright.evaluate(()=>({
    institution: document.body.innerText.includes('[浙江大学图书馆]') ? '浙江大学图书馆' : null,
    items:[...document.querySelectorAll('table tbody tr[data-row-key]')].map(row=>({id:row.getAttribute('data-row-key'),title:row.querySelector('.titleBox a')?.innerText.trim(),metadata:row.querySelector('.timeBox')?.innerText.trim()})).filter(x=>x.title)
  }));
  return {source:'全国报刊索引',query:keyword.trim(),page:1,...result,note:'普通检索首屏题录；包括多种文献类型，机构识别不代表每条全文有权限。'};
}
