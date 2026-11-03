/** Read visible Lippincott Williams & Wilkins titles on the current Ovid book-browse page. */
export async function ovidLwwBooksCurrent(tab, keyword='') {
 if(typeof keyword!=='string'||keyword.length>200)throw Error('关键词长度不能超过200字');
 const d=await tab.playwright.evaluate(()=>({host:location.hostname,page:document.querySelector('h1')?.innerText||'',items:[...document.querySelectorAll('td.newbooklist-textarea')].filter(e=>e.getClientRects().length).map(e=>({title:e.querySelector('h3')?.innerText.replace(/\s+/g,' ').trim()||'',details:e.innerText.replace(/\s+/g,' ').trim()})).filter(x=>x.title&&/Lippincott Williams & Wilkins/i.test(x.details))}));
 if(!/\.ovid\.com$/.test(d.host)||!d.page.includes('电子书')||!d.items.length)throw Error('未确认 Ovid 电子书当前页或 LWW 题录');
 const q=keyword.trim().toLowerCase();return {source:'Ovid 页面中标示 Lippincott Williams & Wilkins 的图书',keyword,items:d.items.filter(x=>x.title.toLowerCase().includes(q)),note:'仅当前可见页按出版商和标题本地筛选；不是全库检索，不输出会话链接或全文。'};
}
