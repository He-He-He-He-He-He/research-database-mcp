/* 人大复印报刊资料，CUA 后台工作页主题词检索第一页。 */
export async function rdfybkSearch(tab,keyword){
 if(typeof keyword!=='string'||!keyword.trim()||keyword.length>100)throw Error('关键词需为 1–100 字');
 const u=new URL('https://www.rdfybk.com/home/allsearch');u.search=new URLSearchParams({s0:'0',s1:keyword.trim(),s9:'主题词'}).toString();u.hash='jieguo';await tab.goto(u.toString());
 try{await tab.playwright.locator('#List tr[data-artid]').first().waitFor({state:'visible',timeoutMs:15000});}catch(_){throw Error('未读取到结果；请检查无结果、登录、验证或页面结构变化。');}
 try{await tab.playwright.getByRole('button',{name:'浙江大学',exact:true}).waitFor({state:'visible',timeoutMs:3000});}catch(_){}
 const data=await tab.playwright.evaluate(()=>({institution:[...document.querySelectorAll('[role=button],button')].some(x=>x.innerText.trim()==='浙江大学')?'浙江大学':null,items:[...document.querySelectorAll('#List tr[data-artid]')].map(r=>{let t=r.querySelectorAll('td'),a=t[0]?.querySelector('a');return {id:r.getAttribute('data-artid'),title:a?.innerText.trim(),url:a?.href,authors:t[1]?.innerText.trim(),journal:t[2]?.innerText.trim(),year:t[3]?.innerText.trim()};}).filter(x=>x.title)}));
 return {source:'人大复印报刊资料',query:keyword.trim(),page:1,...data,note:'首屏主题词检索，全文访问权限未验证。'};
}
