/** 浙大掌阅精选电子书搜索首屏。 */
export async function zhangyueSearch(tab,keyword){
 if(typeof keyword!=='string'||!keyword.trim()||keyword.length>100) throw Error('关键词须为 1–100 字');
 const query=keyword.trim();
 try{await tab.goto('https://se.zhangyue.com/search/index?appId=bf371033&keyword='+encodeURIComponent(query));}catch(e){ /* 页面导航可能超时，以下仍验证内容 */ }
 for(let i=0;i<4;i++){try{await tab.playwright.locator('a[href*="/book/detail?"] .bookname').first().waitFor({state:'visible',timeoutMs:20000});break;}catch(e){if(i===3)throw e;}}
 const items=await tab.playwright.evaluate(()=>Array.from(document.querySelectorAll('a[href*="/book/detail?"]')).filter(a=>a.getClientRects().length).map(a=>({title:a.querySelector('.bookname')?.innerText.trim()||'',author:a.querySelector('.bk_author')?.innerText.trim()||'',publisher:a.querySelector('.bk_publisher')?.innerText.trim()||'',url:a.href})).filter(x=>x.title));
 return {source:'掌阅精选',query,page:1,institution:'浙江大学图书馆频道',items,note:'电子书题录，频道名称不证明机构认证；阅读权限未验证。'};
}
