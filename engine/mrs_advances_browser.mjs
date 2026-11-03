/** Cambridge 的 MRS Advances 期刊归档，非完整 MRS 会议文集。只读取当前页题录。 */
export async function mrsAdvancesPage(tab, query) {
  if (typeof query !== 'string' || !query.trim()) throw Error('关键词不能为空');
  const p = new URLSearchParams({q:query.trim(),searchWithinIds:'84C89204608A187751B818A15F5ECAA0',fts:'yes'});
  await tab.goto('https://www.cambridge.org/core/journals/mrs-advances/listing?'+p);
  await tab.playwright.locator('body').waitFor({state:'visible',timeoutMs:25000});
  return await tab.playwright.evaluate(() => {
    const body=document.body.innerText;
    if (!/results? for .* in MRS Advances/i.test(body) && !/0 results/i.test(body)) throw Error('未确认 MRS Advances 检索结果页面');
    const items=[...document.querySelectorAll('ul.details')].filter(c=>c.getClientRects().length && c.querySelector('a[href*="/core/journals/mrs-advances/article/"]')).map(c=>({
      title:c.querySelector('li.title h3 a')?.innerText.trim(),url:c.querySelector('li.title h3 a')?.href,
      authors:c.querySelector('li.author')?.innerText.trim()||null,
      journal:c.querySelector('a.productParent')?.innerText.trim()||null,
      publication:c.querySelector('dl')?.innerText.trim()||null,
      access:c.querySelector('li.status.entitled')?'entitled':c.querySelector('li.status.get')?'get access':null
    })).filter(x=>x.title && x.journal==='MRS Advances');
    return {source:'MRS Advances（Cambridge 归档）',institution:body.includes('Authenticated by\nZhejiang University')?'Zhejiang University':null,total:(body.match(/([\d,]+) results? for .* in MRS Advances/i)||[])[1]||null,items};
  });
}
