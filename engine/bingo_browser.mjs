/** 冰果英语新闻站的公开内容搜索首屏；非课程检索。 */
export async function bingoSearch(tab,keyword){
 if(typeof keyword!=='string'||!keyword.trim()||keyword.trim().length>100)throw Error('关键词须为 1–100 个字符');
 const query=keyword.trim();await tab.goto('https://lib.bingoenglish.com/content/html/news/');
 await tab.playwright.locator('input[name="keyword"]').fill(query);await tab.playwright.locator('input[type="image"]').first().click();
 await tab.playwright.locator('dl dt a').first().waitFor({state:'visible',timeoutMs:20000});
 const items=await tab.playwright.evaluate(()=>Array.from(document.querySelectorAll('dl')).filter(e=>e.querySelector('dt a')).map(e=>{const a=e.querySelector('dt a');const spans=Array.from(e.querySelectorAll('dd span')).map(x=>x.innerText.trim());return {title:a.innerText.trim(),url:a.href,metadata:spans.filter(x=>!x.startsWith('/content/'))};}));
 return {source:'冰果英语内容搜索',query,page:1,items,note:'新闻站公开内容搜索，可能含图文及视频；课程与全文权限未验证。'};
}
