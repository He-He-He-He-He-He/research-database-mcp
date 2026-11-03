/* 读秀图书首屏检索，供 Codex CUA 工作 Tab 使用。 */
export async function duxiuBookSearch(tab,keyword){
 if(typeof keyword!=='string'||!keyword.trim()||keyword.length>100)throw Error('关键词需 1–100 字');
 const u=new URL('https://book.duxiu.com/search');u.search=new URLSearchParams({Field:'all',channel:'search',sw:keyword.trim(),ecode:'utf-8',edtype:'',searchtype:'',view:'0'}).toString();await tab.goto(u.toString()); await tab.getAXState({emit:false});
 await tab.getAXState({emit:false});
 const data=await tab.playwright.evaluate(()=>({institution:document.body.innerText.includes('欢迎来自浙江大学的朋友')?'浙江大学':null,items:[...document.querySelectorAll('.books-title')].map(t=>{let a=t.querySelector('a'),dl=t.closest('dl');return {title:a?.innerText.trim(),url:a?.href,fields:[...dl.querySelectorAll('dd')].map(e=>e.innerText.trim()).filter(x=>/^(作者|出版日期|丛书名|简介|ISBN|主题词)\s*[:：]/.test(x))};}).filter(x=>x.title)}));
 if(!data.items.length) throw Error('未读取到结果，请检查无结果、登录、验证码或结构变化。');
 return {source:'读秀学术搜索',query:keyword.trim(),page:1,...data,note:'图书首屏题录；全文、文献传递和阅读权限尚未验证。'};
}
