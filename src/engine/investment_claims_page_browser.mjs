/** 读取 Investment Claims 普通检索的指定页；只返回页面题录。 */
export async function investmentClaimsPage(tab, query, page = 1) {
  if (typeof query !== 'string' || !query.trim() || query !== query.trim() || query.length > 100) throw Error('关键词需为 1–100 字');
  if (!Number.isSafeInteger(page) || page < 1 || page > 1000) throw Error('页码需为 1–1000 的整数');
  const u = new URL('https://oxia.ouplaw.com/search');
  for (const [k, v] of Object.entries({access:'all',level:'all',page:String(page),pageSize:'20',prd:'IC',q:query,sort:'relevance'})) u.searchParams.set(k,v);
  await tab.goto(u.href);
  for (let i = 0; i < 20; i++) {
    const d = await tab.playwright.evaluate(() => {
      const u = new URL(location.href);
      const m = document.body.innerText.match(/You are looking at\s+([\d,]+)\s*[–-]\s*([\d,]+)\s+of\s+([\d,]+)\s+results/i);
      const items = [...document.querySelectorAll('.contentItem')].filter(e => e.querySelector('h2.itemTitle a')).map(e => {
        const a = e.querySelector('h2.itemTitle a'), meta = {};
        for (const x of e.querySelectorAll('dl.metadata')) { const k=x.querySelector('dt')?.innerText.trim(), v=x.querySelector('dd')?.innerText.trim(); if(k&&v) meta[k]=v; }
        const link = new URL(a.href);
        return {title:a.innerText.replace(/\s*»\s*$/,'').trim(),url:link.origin+link.pathname,authors:e.querySelector('.itemAuthor')?.innerText.trim()||null,contentType:meta['Content type']||null,citation:meta.Citation||null,product:meta.Product||null};
      });
      return {host:u.hostname,path:u.pathname,q:u.searchParams.get('q'),product:u.searchParams.get('prd'),page:Number(u.searchParams.get('page')),first:m?Number(m[1].replaceAll(',','')):null,last:m?Number(m[2].replaceAll(',','')):null,total:m?Number(m[3].replaceAll(',','')):null,items};
    });
    if (d.host==='oxia.ouplaw.com' && d.path==='/search' && d.q===query && d.product==='IC' && d.page===page && d.first===(page-1)*20+1 && d.items.length===d.last-d.first+1 && d.items.every(x=>x.title&&x.product==='Investment Claims [IC]'))
      return {source:'Oxford Investment Claims',query,page,total:d.total,first:d.first,last:d.last,items:d.items,note:'公开普通检索页题录；过滤需授权，未验证学校订购或全文权限。'};
    await new Promise(resolve=>setTimeout(resolve,500));
  }
  throw Error('未确认请求的 Investment Claims 结果页；可能无结果、超出页数或需要授权');
}
