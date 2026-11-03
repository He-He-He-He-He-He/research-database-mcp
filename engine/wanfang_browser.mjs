/* 供 Codex CUA 的浏览器 Tab 使用，调用者提供专门创建的后台工作标签页。只读第一页或指定页，不下载全文。 */
export async function wanfangSearch(tab, keyword, page=1, category='paper') {
  if (typeof keyword !== 'string' || !keyword.trim() || keyword.length>100 || !Number.isInteger(page) || page<1 || page>100) throw new Error('关键词或页码不合法');
  if (!['paper','thesis','conference','patent','nstr','standard','law','cstad'].includes(category)) throw new Error('目前仅支持实测的期刊（paper）、学位（thesis）会议论文（conference）、专利（patent）、科技报告（nstr）、标准（standard）法规（law）和科技成果（cstad）');
  const url='https://s.wanfangdata.com.cn/'+category+'?'+new URLSearchParams({q:keyword.trim(),p:String(page)}).toString();
  await tab.goto(url);
  try { await tab.playwright.locator('.normal-list .title-area .title').first().waitFor({state:'visible',timeoutMs:15000}); }
  catch (_) { throw new Error('没有读取到结果，请检查上游页面、网络、登录、人机校验或是否无结果；不自动重试。'); }
  const result=await tab.playwright.evaluate(() => {
    const items=[...document.querySelectorAll('.normal-list')].map(e=>({
      title:e.querySelector('.title-area .title')?.textContent.trim(),
      id:e.querySelector('.title-id-hidden')?.textContent.trim(),
      type:e.querySelector('.essay-type')?.textContent.trim(),
      journal:e.querySelector('.periodical-title')?.textContent.trim(),
      author_line:e.querySelector('.author-area')?.innerText.trim(),
      abstract:e.querySelector('.abstract-area')?.innerText.trim(),
      keywords:[...e.querySelectorAll('.keywords-list')].map(x=>x.innerText.trim())
    })).filter(x=>x.title);
    const actualPage=new URL(location.href).searchParams.get('p');
    const activePage=document.querySelector('.bottom-pagination .pager.active')?.textContent.trim() || null;
    return {institution:document.body.innerText.includes('浙江大学图书馆')?'浙江大学图书馆':null,items,actualPage,activePage};
  });
  if(result.actualPage!==String(page) || (result.activePage!==null && result.activePage!==String(page))) throw new Error('万方实际页码与请求不一致；可能发生重定向或结果尚未更新');
  delete result.actualPage; delete result.activePage;
  return {source:'万方知识服务平台',category,page,url,...result,note:'题录为当前页面内容；摘要可能截断，机构标识不保证全文权限。'};
}
