/** 超星期刊检索首屏题录；通过调用者的已授权浏览器标签执行。 */
export async function chaoxingJournalsSearch(tab, query) {
  if (typeof query !== 'string' || !query.trim() || query.length > 100 || /[\x00-\x1f]/.test(query)) throw Error('关键词须为 1–100 字且不含控制字符');
  const term = query.trim();
  const url = 'https://qikan.chaoxing.com/searchjour?' + new URLSearchParams({sw: term, topsearch:'0', size:'50'});
  try { await tab.goto(url); } catch (e) {
    if (!String(e).includes('Timed out waiting for tab')) throw e;
  }
  let d;
  for (let i=0;i<10;i++) {
    await tab.getAXState({emit:false});
    d = await tab.playwright.evaluate(() => ({url:location.href, body:document.body.innerText.slice(0,20000), items:[...document.querySelectorAll('table.listTable tr')].slice(1).filter(r=>r.getClientRects().length).map(r=>{const c=[...r.querySelectorAll(':scope > td')].map(x=>x.innerText.trim());return c.length>=8&&c[1]?{title:c[1],authors:c[2],journal:c[3],section:c[4],year_issue:c[5],citations:c[6],reads:c[7]}:null}).filter(Boolean)}));
    const u = new URL(d.url);
    if (u.hostname !== 'qikan.chaoxing.com' || u.pathname !== '/searchjour' || u.searchParams.get('sw') !== term) throw Error('未到达对应检索页，可能发生登录或验证跳转');
    if (/验证码|安全验证/.test(d.body)) throw Error('出现安全验证，已停止');
    if (/共检索到\s*[\d,]+\s*个结果/.test(d.body) && (d.items.length || /共检索到\s*0\s*个结果/.test(d.body))) break;
  }
  const m = d.body.match(/共检索到\s*([\d,]+)\s*个结果/);
  if (!m || (Number(m[1].replaceAll(',',''))>0 && !d.items.length)) throw Error('结果未加载完成，无法区分加载失败和空结果');
  return {source:'超星期刊',query:term,institution:d.body.includes('欢迎来自浙江大学的朋友')?'浙江大学':null,total:Number(m[1].replaceAll(',','')),items:d.items,note:'全部范围检索结果首屏题录；机构欢迎语不证明全文权限，未读取全文。'};
}
