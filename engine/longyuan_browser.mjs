/* 龙源浙大电子阅览室：单页按刊名查询，不读取全文。 */
export async function longyuanMagazineSearch(tab,keyword) {
  if(typeof keyword!=='string'||!keyword.trim()||keyword.length>100) throw Error('刊名关键词需为 1–100 字');
  const url='https://zju.dps.qikan.cn/pc/index#/searchResults/magazine/'+encodeURIComponent(keyword.trim());
  await tab.goto(url);
  try {await tab.playwright.locator('.list-item h5').first().waitFor({state:'visible',timeoutMs:15000});}
  catch (_) {throw Error('未读取到期刊，请检查无结果、登录、验证或页面变化。');}
  const data=await tab.playwright.evaluate(()=>({institution:document.body.innerText.includes('浙江大学电子阅览室')?'浙江大学电子阅览室':null,items:[...document.querySelectorAll('.list-item')].map(e=>({title:e.querySelector('h5')?.innerText.trim(),issue:e.querySelector('span')?.innerText.trim()})).filter(x=>x.title)}));
  return {source:'龙源浙江大学电子阅览室',query:keyword.trim(),url,...data,note:'刊名搜索的当前页，全文权限未核实。'};
}
