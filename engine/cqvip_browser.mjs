/* 使用 Codex CUA 后台工作 Tab；正常网页检索并读取当前首屏题录。 */
export async function cqvipSearch(tab, keyword) {
  if(typeof keyword !== 'string' || !keyword.trim() || keyword.length>100) throw new Error('关键词需为 1–100 字');
  await tab.goto('https://qikan.cqvip.com/');
  await tab.playwright.locator('#searchKeywords').fill(keyword.trim());
  await tab.playwright.locator('#btnSearch').click();
  try { await tab.playwright.locator('#remark dl dt a[articleid]').first().waitFor({state:'visible',timeoutMs:15000}); }
  catch (_) { throw new Error('未读取到结果，请检查无结果、访问限制、验证码或页面改版；不自动重试。'); }
  const items=await tab.playwright.evaluate(() => [...document.querySelectorAll('#remark dl')].map(e=>{
    const a=e.querySelector('dt a[articleid]'); const ds=[...e.querySelectorAll(':scope > dd')].filter(x=>!x.classList.contains('no')&&!x.classList.contains('sel')&&!x.classList.contains('source'));
    return {title:a?.textContent.trim(),id:a?.getAttribute('articleid'),url:a?.href,author_source:ds[0]?.innerText.trim(),abstract:ds[1]?.innerText.replace(/展开更多\s*$/,'').trim(),keywords:ds[2]?.innerText.replace(/^关键词\s*[:：]?/,'').trim()};
  }).filter(x=>x.title));
  return {source:'维普中文期刊服务平台',query:keyword.trim(),page:1,items,note:'首屏题录，摘要可能截断；是否已获浙大机构认证及全文权限尚未核实。'};
}
