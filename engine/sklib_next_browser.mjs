/** 在已加载的中国社会科学文库首页检索结果中前进到第 2 页。 */
export async function sklibNext(tab){
 const read=()=>tab.playwright.evaluate(()=>{const u=new URL(location.href),text=document.body.innerText,m=text.match(/([\d,]+)\s*个检索结果/);return {host:u.hostname,path:u.pathname,query:document.querySelector('#queryText')?.value,page:Number(document.querySelector('#pageBar .curr')?.innerText),total:m?Number(m[1].replaceAll(',','')):null,items:[...document.querySelectorAll('#img-data-list .list-item')].map(e=>({title:e.querySelector('.list-item__title')?.innerText.trim()||null,type:e.querySelector('h4 .tab.pc')?.innerText.trim()||null})).filter(x=>x.title)};});
 const before=await read();if(before.host!=='www.sklib.cn'||before.path!=='/booklib/search'||before.page!==1||!before.query||!before.items.length)throw Error('需先在当前标签打开社科文库普通检索第 1 页');
 await tab.playwright.locator('#pageBar a[page-index="2"]').first().click();
 for(let i=0;i<20;i++){const d=await read();if(d.host===before.host&&d.path===before.path&&d.query===before.query&&d.page===2&&d.total===before.total&&d.items.length&&d.items[0].title!==before.items[0].title)return {source:'中国社会科学文库',query:d.query,page:2,total:d.total,items:d.items,note:'页面第 2 页可见题录；不读取摘要或全文。'};await new Promise(resolve=>setTimeout(resolve,500));}
 throw Error('未确认第 2 页结果；可能需要登录或安全验证');
}
