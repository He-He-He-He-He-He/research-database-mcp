/**
 * 中国裁判文书网：面向 Codex CUA 的已登录页面只读适配器。
 * 由使用者提供当前会话的 tab；不读取、复制或保存 Cookie 和账号信息。
 * 不可当作独立 HTTP API 使用。页面由用户或浏览器工具正常打开并搜索。
 */
export async function readWenshuList(tab) {
  const url = await tab.url();
  if (!url?.startsWith('https://wenshu.court.gov.cn/website/wenshu/181217BMTKHNT2W0/')) throw new Error('请先打开已登录的文书列表页');
  const result = await tab.playwright.evaluate(() => {
    const items = [...document.querySelectorAll('.LM_list')].map(e => ({
      title:e.querySelector('.caseName')?.textContent?.trim(),
      url:e.querySelector('.caseName')?.href,
      court:e.querySelector('.slfyName')?.textContent?.trim(),
      caseNo:e.querySelector('.ah')?.textContent?.trim(),
      date:e.querySelector('.cprq')?.textContent?.trim(),
      summary:e.querySelector('.list_reason p')?.textContent?.trim()
    })).filter(e=>e.title && e.url);
    return {items};
  });
  if (!result.items.length) throw new Error('未读到列表；可能正在加载、无结果、登录失效或要求验证，请检查页面');
  return {...result, note:'只读取当前页面；查询条件需在网页核验，详情链接可能有时效'};
}
export async function readWenshuDetail(tab) {
  const url = await tab.url();
  if (!url?.startsWith('https://wenshu.court.gov.cn/website/wenshu/181107ANFZ0BXSK4/')) throw new Error('请先打开已登录的文书全文页');
  const result=await tab.playwright.evaluate(() => ({text:document.querySelector('.PDF_pox')?.innerText?.trim()||''}));
  if (!result.text) throw new Error('未读取到正文；请检查登录、页面加载或验证状态');
  return {...result, note:'原文来自当前页面，可能含个人信息；不默认保存或传播'};
}
export async function searchWenshu(tab, keyword) {
  if (typeof keyword !== 'string' || !keyword.trim() || keyword.length>100) throw new Error('关键词需为 1–100 字');
  await tab.goto('https://wenshu.court.gov.cn/');
  const box=tab.playwright.locator('input.searchKey');
  await box.waitFor({state:'visible',timeoutMs:15000});
  await box.fill(keyword.trim());
  await box.press('Enter');
  try {
    await tab.playwright.getByText('全文：'+keyword.trim()).waitFor({state:'visible',timeoutMs:20000});
    await tab.playwright.locator('.LM_list .caseName').first().waitFor({state:'visible',timeoutMs:20000});
  } catch (_) { throw new Error('检索未显示对应条件和结果；请检查登录、无结果或验证要求，不自动重试'); }
  return await readWenshuList(tab);
}
