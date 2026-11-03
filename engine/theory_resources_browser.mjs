/** 中国共产党思想理论资源数据库校园网图书搜索单页。 */
export async function theoryResourcesSearch(tab,keyword){
 if(typeof keyword!=='string'||!keyword.trim()||keyword.trim().length>100)throw Error('关键词须为 1–100 个字符');
 const query=keyword.trim();await tab.goto('http://10.203.97.151/');
 await tab.playwright.locator('#searchText').fill(query);await tab.playwright.getByText('按图书检索',{exact:true}).click();
 await tab.playwright.locator('.searchList .list_item .infoTitle').first().waitFor({state:'visible',timeoutMs:20000});
 const data=await tab.playwright.evaluate(()=>{const raw=document.querySelector('.totalCount')?.innerText?.trim();const valid=typeof raw==='string'&&/^(?:\d+|\d{1,3}(?:,\d{3})+)$/.test(raw);const value=valid?Number(raw.replaceAll(',','')):null;return {total:Number.isSafeInteger(value)?value:null,items:Array.from(document.querySelectorAll('.searchList .list_item')).map(e=>({title:e.querySelector('.infoTitle')?.innerText.trim()||'',metadata:Array.from(e.querySelectorAll('.infoLabel')).map(x=>x.innerText.trim())})).filter(x=>x.title)}});
 return {source:'中国共产党思想理论资源数据库',query,page:1,...data,note:'校园内部资源，图书题录首屏；全文未验证，无结果或页面变化可能超时。'};
}
