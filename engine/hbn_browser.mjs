/** HBN：只读取当前数据中心页面已选择的表格，不改变选择或下载。 */
export async function hbnReadCurrentTable(tab){
 const data=await tab.playwright.evaluate(()=>({url:location.href,institution:document.body.innerText.includes('浙江大学')?'浙江大学':null,columns:Array.from(document.querySelectorAll('.ant-table-thead th')).filter(e=>e.getClientRects().length).map(e=>e.innerText.trim()),rows:Array.from(document.querySelectorAll('.ant-table-tbody tr')).filter(e=>e.getClientRects().length).map(e=>Array.from(e.querySelectorAll('td')).map(x=>x.innerText.trim()))}));
 if(!data.url.startsWith('https://data.harborn.cn/data/index')||!data.columns.length||!data.rows.length)throw Error('当前页没有可读取的数据表，可能尚未选择指标、加载未完成或权限不足');
 return {source:'HBN环球财经系列数据库',...data,note:'当前页面已显示的数据，单位和来源需结合所选指标说明；未验证其他指标或下载权限。'};
}
