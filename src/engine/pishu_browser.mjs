/* 皮书数据库的单页关键词检索；在 Codex CUA 工作页上运行。 */
export async function pishuSearch(tab,keyword){
 if(typeof keyword!=='string'||!keyword.trim()||keyword.length>100)throw Error('关键词需为 1–100 字');
 const u=new URL('https://www.pishu.com.cn/skwx_ps/search');u.search=new URLSearchParams({query:encodeURIComponent(keyword.trim()),resourceType:'all',field:'All',search:'1',SiteID:'14',firstSublibID:''}).toString();await tab.goto(u.toString());
 try{await tab.playwright.locator('#resultList .searCon_tit a').first().waitFor({state:'visible',timeoutMs:15000});}catch(_){throw Error('未读取结果，请检查无结果、登录、验证或页面改变。');}
 const data=await tab.playwright.evaluate(()=>({institution:document.querySelector('#span_branchlogout')?.innerText.includes('浙江大学图书馆')?'浙江大学图书馆':null,items:[...document.querySelectorAll('#resultList .searCon')].map(e=>{const a=e.querySelector('.searCon_tit a');return {title:a?.innerText.trim(),url:a?.href,type:e.querySelector('.searCon_tit em')?.innerText.trim(),abstract:e.querySelector('.searCon_con')?.innerText.trim(),metadata:[...e.querySelectorAll('.searIntro')].map(x=>x.innerText.trim())};}).filter(x=>x.title)}));
 return {source:'皮书数据库',query:keyword.trim(),page:1,...data,note:'首屏结果，摘要可能截断，机构标识不保证全文权限。'};
}
