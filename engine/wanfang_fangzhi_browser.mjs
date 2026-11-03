/* 万方地方志数据库整书首屏检索，使用 Codex CUA 工作页。 */
export async function wanfangFangzhiSearch(tab,keyword){
 if(typeof keyword!=='string'||!keyword.trim()||keyword.length>100)throw Error('关键词需为 1–100 字');
 const u=new URL('https://fz.wanfangdata.com.cn/search/tlc');u.search=new URLSearchParams({q:keyword.trim()}).toString();await tab.goto(u.toString());
 try{await tab.playwright.locator('.centerBox .centerRight .titleLeft p.title').first().waitFor({state:'visible',timeoutMs:15000});}catch(_){} await tab.getAXState({emit:false});
 const data=await tab.playwright.evaluate(()=>({institution:document.body.innerText.includes('浙江大学图书')?'浙江大学图书馆（页面显示）':null,items:[...document.querySelectorAll('.centerBox')].map(e=>({title:e.querySelector('.titleLeft p.title')?.textContent.trim(),type:e.querySelector('.typeBox')?.innerText.trim(),metadata:e.querySelector('.info')?.innerText.trim()})).filter(x=>x.title)}));
 if(!data.items.length)throw Error('未读取结果，请检查无结果、登录、验证或页面结构变化。');
 return {source:'万方中国地方志数据库',query:keyword.trim(),page:1,...data,note:'仅志书首页题录；馆藏机构标识与全文权限需要分别核验。'};
}
