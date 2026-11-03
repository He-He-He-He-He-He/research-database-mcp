/** 广州大典馆藏题录：通过 CUA 查询首屏。 */
export async function guangzhouDadianSearch(tab,keyword) {
 if(typeof keyword!=='string'||!keyword.trim()||keyword.length>100) throw Error('关键词须为 1–100 个字符');
 const query=keyword.trim();
 await tab.goto('https://gzdd.gzlib.org.cn/website/index');
 await tab.playwright.getByPlaceholder('请输入检索内容').fill(query);
 await tab.playwright.getByRole('button',{name:'大典检索'}).click();
 await tab.playwright.locator('table.el-table__body tbody tr').first().waitFor({state:'visible',timeoutMs:20000});
 const items=await tab.playwright.evaluate(()=>Array.from(document.querySelectorAll('table.el-table__body tbody tr')).map(r=>{
   const c=Array.from(r.querySelectorAll('td')).map(x=>x.innerText.trim());
   return {title:c[0]||'',responsibility:c[1]||'',division:c[2]||'',series:c[3]||'',volume:c[4]||'',edition:c[5]||''};
 }));
 return {source:'广州大典数据库',query,page:1,institution:null,items,note:'题录首屏；未见机构标识，影像与全文权限未验证；空结果可能超时。'};
}
