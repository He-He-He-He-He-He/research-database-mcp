/* 书同文清实录：单页命中目录，仅记录路径和链接。 */
export async function shutongwenQslSearch(tab,keyword){
 if(typeof keyword!=='string'||!keyword.trim()||keyword.length>100)throw Error('关键词需为 1–100 字');
 await tab.goto('https://gujiku.unihan.com.cn/Products/Search/QSL');
 await tab.playwright.locator('#sv_0').fill(keyword.trim());
 await tab.playwright.getByRole('button',{name:'搜索',exact:true}).click();
 try{await tab.playwright.locator('a.list-group-item[data-pageid]').first().waitFor({state:'visible',timeoutMs:20000});}catch(_){throw Error('未读取清实录结果；可能无结果、权限不足或页面变化。');}
 const data=await tab.playwright.evaluate(()=>({items:[...document.querySelectorAll('a.list-group-item[data-pageid]')].map(a=>({path:a.querySelector('h4')?.innerText.trim(),pageId:a.dataset.pageid,url:a.href})).filter(x=>x.path)}));
 return {source:'书同文清实录',query:keyword.trim(),page:1,...data,note:'仅首屏命中路径；权限取决于当前机构会话。'};
}
