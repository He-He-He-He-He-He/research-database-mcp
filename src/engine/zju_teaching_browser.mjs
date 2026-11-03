/** 浙大教参服务平台：需要用户已有登录会话，仅查询单页题录。 */
export async function zjuTeachingSearch(tab,keyword) {
 if(typeof keyword!=='string'||!keyword.trim()||keyword.trim().length>100) throw Error('关键词须为 1–100 个字符');
 const query=keyword.trim();
 const criteria={searchval:query,searchfield:'title',searchtype:'match_phrase',condition:'and'};
 await tab.goto('https://jc.zju.edu.cn/collection/list?SearchQuery='+encodeURIComponent(JSON.stringify(criteria)));
 await tab.playwright.locator('.list-box .book-title').first().waitFor({state:'visible',timeoutMs:20000});
 const items=await tab.playwright.evaluate(()=>Array.from(document.querySelectorAll('.list-box')).map(e=>({title:e.querySelector('.book-title > span')?.innerText.trim()||'',type:e.querySelector('.book-type')?.innerText.trim()||'',fields:Array.from(e.querySelectorAll('.col-box')).map(x=>({label:x.querySelector('b')?.innerText.trim()||'',value:x.querySelector('span')?.innerText.trim()||''})).filter(x=>x.label)})).filter(x=>x.title));
 return {source:'浙大教参服务平台',query,page:1,items,note:'依赖既有登录会话，当前页题录；全文和下载权限未验证。无结果或页面变化可能超时。'};
}
