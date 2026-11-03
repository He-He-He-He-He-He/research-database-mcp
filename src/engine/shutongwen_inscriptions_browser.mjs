/** 书同文历代石刻史料汇编单页结果路径。 */
export async function inscriptionsSearch(tab,keyword){
 if(typeof keyword!=='string'||!keyword.trim()||keyword.trim().length>100)throw Error('关键词须为 1–100 个字符');
 const query=keyword.trim();await tab.goto('https://gujiku.unihan.com.cn/Products/Search/LDSK');
 await tab.playwright.locator('#sv_0').fill(query);await tab.playwright.getByRole('button',{name:'搜索',exact:true}).click();
 await tab.playwright.locator('a.list-group-item[data-pageid]').first().waitFor({state:'visible',timeoutMs:20000});
 const items=await tab.playwright.evaluate(()=>Array.from(document.querySelectorAll('a.list-group-item[data-pageid]')).filter(e=>e.getClientRects().length).map(a=>({path:a.querySelector('h4')?.innerText.trim()||'',pageId:a.dataset.pageid,url:a.href})).filter(x=>x.path));
 return {source:'书同文历代石刻史料汇编',query,page:1,items,note:'首屏命中目录路径，具体阅读权限未验证。'};
}
