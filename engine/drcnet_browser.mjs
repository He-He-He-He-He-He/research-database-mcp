/* 国研网教育版题名检索，返回首屏。调用者须提供 CUA 后台工作 Tab。 */
export async function drcnetSearch(tab,keyword){
 if(typeof keyword!=='string'||!keyword.trim()||keyword.length>100)throw Error('关键词需为 1–100 字');
 const u=new URL('https://search.drcnet.com.cn/simpleSearch');u.search=new URLSearchParams({word:keyword.trim(),type:'1',rootlm:'20548',attrIndex:'',classification1:''}).toString();await tab.goto(u.toString());
 try{await tab.playwright.locator('a.article-title-link').first().waitFor({state:'visible',timeoutMs:15000});}catch(_){}
 await tab.getAXState({emit:false});
 const data=await tab.playwright.evaluate(()=>({institution:document.body.innerText.includes('欢迎您，浙江大学图书馆')?'浙江大学图书馆':null,items:[...document.querySelectorAll('tr.el-table__row')].map(r=>{let a=r.querySelector('a.article-title-link');return {title:a?.innerText.trim(),url:a?.href,authors:r.querySelector('.article-author')?.innerText.trim(),date:r.querySelector('.article-date')?.innerText.trim()};}).filter(x=>x.title)}));
 if(!data.items.length)throw Error('未读取结果；请检查无结果、登录、验证或网页结构变化。');
 return {source:'国研网教育版',query:keyword.trim(),page:1,...data,note:'标题检索首屏题录；机构标识不保证全文或统计指标数据权限。'};
}
