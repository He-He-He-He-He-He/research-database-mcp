/* 在数字方志已有检索结果页读取下一页题录；须校园内网。 */
export async function digitalFangzhiNext(tab, keyword) {
  if(typeof keyword !== 'string' || !keyword.trim() || keyword.length > 12) throw Error('关键词需为 1–12 字');
  const q=keyword.trim();
  const before=await tab.playwright.evaluate(() => ({institution:document.body.innerText.includes('欢迎您：浙江大学'), current:Number(document.querySelector('#page_index')?.innerText.match(/\d+/)?.[0]), totalPages:Number(document.querySelector('#page_count')?.innerText.match(/\d+/)?.[0]), query:[...document.querySelectorAll('a')].find(a=>a.href.startsWith('https://www.baidu.com/s?')||a.href.startsWith('http://www.baidu.com/s?'))?.innerText.trim()}));
  if(!before.institution || !before.current || before.query!==q) throw Error('须先在浙江大学方志结果页确认同一检索词');
  if(before.current>=before.totalPages) throw Error('已是最后一页');
  await tab.playwright.locator('#page_next a').click();
  for(let i=0;i<20;i++){
    const r=await tab.playwright.evaluate(() => ({institution:document.body.innerText.includes('欢迎您：浙江大学'),page:Number(document.querySelector('#page_index')?.innerText.match(/\d+/)?.[0]),pages:Number(document.querySelector('#page_count')?.innerText.match(/\d+/)?.[0]),query:[...document.querySelectorAll('a')].find(a=>a.href.startsWith('https://www.baidu.com/s?')||a.href.startsWith('http://www.baidu.com/s?'))?.innerText.trim(),items:[...document.querySelectorAll('#ulComments tr')].slice(1).map(row=>{const c=[...row.querySelectorAll('td')];return c.length>=5?{number:Number(c[0].innerText.trim()),title:c[1].innerText.trim(),section:c[2].innerText.trim(),edition:c[3].innerText.trim(),publication:c[4].innerText.trim(),url:c[1].querySelector('a')?.href}:null}).filter(Boolean)}));
    if(r.institution && r.query===q && r.page===before.current+1 && r.items.length && r.items[0].number===(r.page-1)*15+1) return {source:'中国数字方志库',query:q,...r,note:'校园内网题录，同一本按章节重复；全文未验证。'};
    await new Promise(resolve=>setTimeout(resolve,500));
  }
  throw Error('未确认下一页结果');
}
