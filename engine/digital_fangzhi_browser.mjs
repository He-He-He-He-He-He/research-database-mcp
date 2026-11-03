/* 浙大馆藏中国数字方志库：校园网内单次题录检索，不访问全文。 */
export async function digitalFangzhiSearch(tab,keyword){
 if(typeof keyword!=='string'||!keyword.trim()||keyword.length>12)throw Error('关键词需为 1–12 字');
 await tab.goto('http://10.15.61.5/');
 await tab.playwright.locator('#SearchKeyword').fill(keyword.trim());
 await tab.playwright.locator('#Seach').first().click();
 try{await tab.playwright.locator('#ulComments tr a[href*="BookDetails.aspx"]').first().waitFor({state:'visible',timeoutMs:15000});}catch(_){throw Error('未读取题录，可能无结果、校园网络不可用或页面变化。');}
 const data=await tab.playwright.evaluate(()=>({institution:document.body.innerText.includes('欢迎您：浙江大学')?'浙江大学':null,items:[...document.querySelectorAll('#ulComments tr')].slice(1).map(r=>{const c=[...r.querySelectorAll('td')];return c.length>=5?{title:c[1].innerText.trim(),section:c[2].innerText.trim(),edition:c[3].innerText.trim(),publication:c[4].innerText.trim(),url:c[1].querySelector('a')?.href}:null}).filter(Boolean)}));
 return {source:'中国数字方志库',query:keyword.trim(),page:1,...data,note:'校园内网题录首屏；同一本可能按章节重复，全文权限未验证。'};
}
