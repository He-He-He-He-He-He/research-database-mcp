/* 书同文清会典：单页命中路径，不读取正文。 */
export async function shutongwenQhdSearch(tab,keyword){
 if(typeof keyword!=='string'||!keyword.trim()||keyword.length>100)throw Error('关键词需为1–100字');
 await tab.goto('https://gujiku.unihan.com.cn/Products/Search/QHD');
 await tab.playwright.locator('#sv_0').fill(keyword.trim());
 await tab.playwright.getByRole('button',{name:'搜索',exact:true}).click();
 try{await tab.playwright.locator('a.list-group-item[data-pageid]').first().waitFor({state:'visible',timeoutMs:20000});}catch(_){throw Error('未读取清会典结果；可能无结果、权限不足或页面变化。');}
 const data=await tab.playwright.evaluate(()=>({items:[...document.querySelectorAll('a.list-group-item[data-pageid]')].map(a=>({path:a.querySelector('h4')?.innerText.trim(),pageId:a.dataset.pageid,url:a.href})).filter(x=>x.path)}));
 if(!data.items.length||data.items.some(x=>!x.path.includes('清会典')))throw Error('未确认清会典子库结果');
 return {source:'书同文清会典',query:keyword.trim(),page:1,...data,note:'仅首屏命中路径；机构会话或全文权限需在原站确认。'};
}
