/** 维普期刊单次目录检索，需注入受支持的 CUA 标签。
 * 通过网站搜索控件读取网页结果；不访问下载，不使用账号密码或 Cookie。
 */
export async function searchCQVIP(tab, keyword) {
  if (typeof keyword !== 'string' || !keyword.trim() || keyword.length > 100 || /[\r\n]/.test(keyword))
    throw new Error('关键词必须为 1–100 字的单行文本');
  const query=keyword.trim();
  const initial=await tab.getAXState({emit:false,disableDiffing:true});
  if(!initial.includes('qikan.cqvip.com/')) throw new Error('请先绑定维普期刊页面');
  const field=tab.playwright.getByPlaceholder('请输入检索词').first();
  await field.fill(query);
  await tab.playwright.expectNavigation(()=>tab.playwright.getByRole('button',{name:' 检索'}).click(),{timeoutMs:20000});
  const page=await tab.playwright.evaluate(()=>{
    const query=document.querySelector('#searchKeywords')?.value;
    const count=document.body.innerText.match(/共找到\s*([\d,]+)\s*篇文章/)?.[1];
    const items=[...document.querySelectorAll('dl')].filter(x=>x.getClientRects().length>0 && x.querySelector('dt a[href*="/Qikan/Article/Detail"]')).map(x=>{
      const a=x.querySelector('dt a[href*="/Qikan/Article/Detail"]');
      return {title:a?.innerText||'',url:a?.href||'',details:[...x.querySelectorAll('dd')].map(d=>d.innerText).filter(Boolean)};
    });
    return {query,count:count?Number(count.replaceAll(',','')):null,items};
  });
  if(page.query!==query || page.count===null) throw new Error('搜索结果尚未可确认，或页面结构已经变化');
  return {source:'维普期刊检索页面',...page};
}
