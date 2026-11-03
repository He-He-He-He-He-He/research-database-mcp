/* 台湾学术期刊在线数据库：网页单次文章检索，不下载全文。 */
export async function twsSearch(tab,keyword){
 if(typeof keyword!=='string'||!keyword.trim()||keyword.length>100) throw Error('关键词需为 1–100 字');
 await tab.goto('https://www.twscholar.com/');
 await tab.playwright.locator('#_Search_Field').fill(keyword.trim());
 await tab.playwright.locator('#Search').click();
 try {await tab.playwright.locator('.stageall .stage1 a').first().waitFor({state:'visible',timeoutMs:20000});}
 catch (_) {throw Error('未读取题录，请检查无结果、登录、验证或页面变化。');}
 const data=await tab.playwright.evaluate(()=>({institution:document.body.innerText.includes('浙江大学图书馆，您好')?'浙江大学图书馆':null,items:[...document.querySelectorAll('.stageall')].map(e=>{let a=e.querySelector('.stage1 a');return {title:a?.innerText.trim(),url:a?.href,authors:e.querySelector('.stage2')?.innerText.trim(),publication:e.querySelector('.stage3')?.innerText.trim()};}).filter(x=>x.title)}));
 return {source:'TWS台湾学术期刊',query:keyword.trim(),page:1,...data,note:'首屏文章题录；机构识别不保证全文权限。'};
}
