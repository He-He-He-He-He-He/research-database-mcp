/** 国研网国际贸易系统中国月度默认查询；不保存或导出数据。 */
export async function drcTradeChinaMonthly(tab){
 await tab.goto('https://trade.drcnet.com.cn/data/goods/asia/china/monthly');
 try { await tab.playwright.locator('.el-table__body tbody tr').first().waitFor({state:'visible',timeoutMs:20000}); } catch (_) { /* 某些页面已加载但等待通知超时，下面仍检查实际表格 */ }
 const data=await tab.playwright.evaluate(()=>({institution:document.body.innerText.includes('浙江大学图书馆')?'浙江大学图书馆':null,columns:Array.from(document.querySelectorAll('.el-table__header th')).map(x=>x.innerText.trim()),rows:Array.from(document.querySelectorAll('.el-table__body tbody tr')).filter(x=>x.getClientRects().length).map(x=>Array.from(x.querySelectorAll('td')).map(y=>y.innerText.trim())),selectedOptions:Array.from(document.querySelectorAll('input[type="radio"]:checked')).map(x=>x.closest('label')?.innerText.trim()||'').filter(Boolean)}));
 if (!data.rows.length) throw Error('未读取到月度数据；可能加载失败、无权限或页面变化');
 return {source:'国研网国际贸易研究及决策支持系统',dataset:'中国货物贸易月度',...data,note:'进入页面时默认查询的当前已显示数据；金额单位及查询条件请以页面为准，未验证其他筛选和导出。'};
}
