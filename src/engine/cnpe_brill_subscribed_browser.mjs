/** 从已筛选“已订阅”的中图易阅通 Brill 专题当前页读取题录。 */
export async function cnpeBrillSubscribedCurrent(tab,keyword=''){
 if(typeof keyword!=='string'||keyword.length>200)throw Error('关键词须不超过200字');
 const d=await tab.playwright.evaluate(()=>({host:location.hostname,path:location.pathname,selected:[...document.querySelectorAll('input:checked')].some(x=>x.parentElement?.parentElement?.innerText.trim()==='已订阅'),loading:[...document.querySelectorAll('*')].some(x=>x.children.length===0&&x.innerText?.includes('资源加载中')&&x.getClientRects().length),items:[...document.querySelectorAll('.librarybook')].filter(e=>e.getClientRects().length).map(e=>({title:e.querySelector('.bookTitle .title')?.innerText.trim()||'',author:e.querySelector('.author')?.innerText.trim()||null,press:[...e.querySelectorAll('.press')].map(x=>x.innerText.trim()),isUnlocked:e.querySelector('.icon-unlock')?true:null})).filter(x=>x.title&&x.press.some(t=>/^Brill(?:\s|（|\(|$)/i.test(t)))}));
 if(d.host!=='www.cnpereading.com'||d.path!=='/libraryDetail/brill'||!d.selected||d.loading||!d.items.length)throw Error('未确认 Brill 专题、已订阅筛选或结果加载完成');
 const q=keyword.trim().toLowerCase();return {source:'中图易阅通 Brill 专题已订阅筛选',keyword,items:d.items.filter(x=>x.title.toLowerCase().includes(q)),note:'只读取已订阅筛选当前页的 Brill 标记书目；关键词只在当前页本地筛选。isUnlocked 为 true 表示页面有解锁图标，null 表示未发现图标；学校身份和逐书全文须按原页复核。'};
}
