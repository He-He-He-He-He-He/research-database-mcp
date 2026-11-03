/** 库客音乐图书馆专辑单页检索；不播放或下载。 */
export async function kukeSearch(tab,keyword){
 if(typeof keyword!=='string'||!keyword.trim()||keyword.trim().length>100)throw Error('关键词须为 1–100 个字符');
 const query=keyword.trim();await tab.goto('https://kml.kuke.com/search?keyword='+encodeURIComponent(query)+'&page=1');
 await tab.playwright.locator('dl .message-tit').first().waitFor({state:'visible',timeoutMs:20000});
 const data=await tab.playwright.evaluate(()=>({institution:document.body.innerText.includes('浙江大学')?'浙江大学':null,items:Array.from(document.querySelectorAll('dl')).filter(e=>e.querySelector('.message-tit')).map(e=>{const a=e.querySelector('.message-tit');return {title:a.innerText.trim(),url:a.href,fields:Array.from(e.querySelectorAll('.message-list')).map(x=>({label:x.querySelector('p')?.innerText.trim()||'',value:x.querySelector('span')?.innerText.trim()||''})).filter(x=>x.label)};})}));
 return {source:'库客音乐图书馆',query,page:1,...data,note:'当前页专辑题录；播放和下载权限未验证。'};
}
