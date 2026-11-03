/* 企研机构版：普通搜索数据表目录；只读当前搜索结果，不下载数据。 */
export async function qiyanSearch(tab, keyword) {
  if(typeof keyword!=='string'||!keyword.trim()||keyword.length>100) throw Error('关键词需为 1–100 字');
  await tab.goto('https://r.qiyandata.com/home');
  await tab.playwright.locator('input[readonly][value="请输入关键词搜索数据库/表格等"]').click();
  const normal=tab.playwright.getByText('普通搜索',{exact:true});
  if (await normal.isVisible()) await normal.click();
  const field=tab.playwright.getByPlaceholder('请输入关键词搜索数据库/表格等');
  await field.fill(keyword.trim());
  await field.press('Enter');
  try { await tab.playwright.locator('div[cursor-pointer][b="1 grey-3"]').first().waitFor({state:'visible',timeoutMs:15000}); }
  catch (_) { throw Error('未读取表格目录；可能无结果、登录或页面变化，请检查网页。'); }
  const data=await tab.playwright.evaluate(()=>({institution:document.body.innerText.includes('浙江大学')?'浙江大学':null,items:[...document.querySelectorAll('div[cursor-pointer][b="1 grey-3"]')].slice(0,20).map(e=>({path:e.innerText.trim()}))}));
  return {source:'企研社科大数据平台',query:keyword.trim(),...data,note:'仅返回前 20 条数据表目录，不代表数据下载权限。'};
}

/* 读取已打开的企研表详情；不登录、预览或下载。 */
export async function qiyanTableInfo(tab) {
  try { await tab.playwright.locator('table tbody tr').first().waitFor({state:'visible',timeoutMs:15000}); }
  catch (_) { throw Error('未找到字段说明表，请先在企研打开具体数据表详情。'); }
  const result=await tab.playwright.evaluate(()=>{
    const table=[...document.querySelectorAll('table')].find(t=>{const h=[...t.querySelectorAll('thead th')].map(e=>e.innerText.trim()); return h[0]==='字段' && h[1]==='字段说明';});
    if(!table) return null;
    const root=table.parentElement;
    const text=root.innerText;
    const hint=[...root.querySelectorAll('div')].map(e=>e.innerText.trim()).find(s=>s.startsWith('温馨提示：本表数据区间范围')&&s.length<300)||null;
    const restriction=[...root.querySelectorAll('div')].map(e=>e.innerText.trim()).find(s=>s.startsWith('如需下载/预览数据')&&s.length<300)||null;
    const fields=[...table.querySelectorAll('tbody tr')].map(row=>{const cells=[...row.querySelectorAll('td')].map(e=>e.innerText.trim()); return {name:cells[0],description:cells[1]};}).filter(x=>x.name);
    const yearRange=hint?.match(/(\d{4})年\s*[-—至]\s*(\d{4})年/);
    return {url:location.href,institution:document.body.innerText.includes('浙江大学')?'浙江大学':null,fields,rangeNotice:hint,yearRange:yearRange?{from:Number(yearRange[1]),to:Number(yearRange[2])}:null,restriction};
  });
  if(!result || !result.url.startsWith('https://r.qiyandata.com/data/')) throw Error('当前页面不是可识别的企研表格详情。');
  return {source:'企研社科大数据平台',...result,note:'仅字段说明和页面显示范围；未预览数据值。'};
}
