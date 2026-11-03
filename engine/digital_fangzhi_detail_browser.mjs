/* 只读取中国数字方志库搜索结果提供的书目详情；不操作全文或书架。 */
export async function digitalFangzhiDetail(tab, url) {
  let u; try { u = new URL(url); } catch { throw Error('详情链接无效'); }
  const id=u.searchParams.get('pID'), title=u.searchParams.get('pTitle');
  if(u.origin!=='http://10.15.61.5' || u.pathname!=='/BookDetails.aspx' || !/^[0-9a-f-]{36}$/i.test(id||'') || !title) throw Error('只接受方志库检索返回的详情链接');
  await tab.goto(u.href);
  for(let i=0;i<20;i++) {
    const d=await tab.playwright.evaluate(() => ({institution:document.body.innerText.includes('欢迎您：浙江大学'),id:new URL(location.href).searchParams.get('pID'), fields:[...document.querySelectorAll('#Book_Details tr')].map(row=>{const t=[...row.querySelectorAll(':scope > td')];return t.length===3?{name:t[1].innerText.trim().replace(/[:：]$/,''),value:t[2].innerText.trim()}:null}).filter(x=>x?.name && x.value)}));
    if(d.institution && d.id===id && d.fields.find(x=>x.name==='題名與責任')?.value.includes(title)) return {source:'中国数字方志库',id,title,fields:d.fields,note:'校园内网书目详情，不读取正文或收藏。'};
    await new Promise(resolve=>setTimeout(resolve,500));
  }
  throw Error('未能验证所选书目详情或浙大会话');
}
