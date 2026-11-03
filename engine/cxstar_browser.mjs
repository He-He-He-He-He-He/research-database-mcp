/** 畅想之星全库题录搜索，读取首屏。 */
export async function cxstarSearch(tab,keyword){
 if(typeof keyword!=='string'||!keyword.trim()||keyword.length>100) throw Error('关键词须为 1–100 字');
 const query=keyword.trim();
 await tab.goto('https://www.cxstar.com/Book/Search?keyword='+encodeURIComponent(query)+'&searchType=ALL&packageruid=null');
 for(let i=0;i<3;i++){try{await tab.playwright.locator('.book-list-content .list_title a').first().waitFor({state:'visible',timeoutMs:20000});break;}catch(e){if(i===2)throw e;}}
 const data=await tab.playwright.evaluate(()=>({institution:document.title.includes('浙江大学')?'浙江大学':null,items:Array.from(document.querySelectorAll('.book-list-content')).map(e=>{const a=e.querySelector('.list_title a');const p=e.querySelector('.book-publisher')?.innerText||'';return a?{title:a.innerText.trim(),url:a.href,author:(e.querySelector('.listbook-author')?.innerText||'').replace('作者：','').trim(),publication:p.replace(/\s+/g,' ').trim()}:null}).filter(Boolean)}));
 return {source:'畅想之星',query,page:1,...data,note:'全库题录含已购及未购，页面标识不证明每条阅读权限。'};
}
