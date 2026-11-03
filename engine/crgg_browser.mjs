/** 国别区域与全球治理数据平台资源首屏。 */
export async function crggSearch(tab,keyword){
 if(typeof keyword!=='string'||!keyword.trim()||keyword.length>100) throw Error('关键词须为 1–100 字');
 const query=keyword.trim();
 await tab.goto('https://www.crggcn.com/skwx_crgg/search?query='+encodeURIComponent(encodeURIComponent(query))+'&resourceType=all&field=All&search=1&SiteID=25');
 for(let i=0;i<3;i++){try{await tab.playwright.locator('#resultList h5 a').first().waitFor({state:'visible',timeoutMs:20000});break;}catch(e){if(i===2)throw e;}}
 const data=await tab.playwright.evaluate(()=>({institution:document.querySelector('#span_branchlogout')?.innerText.includes('浙江大学图书馆')?'浙江大学图书馆':null,items:Array.from(document.querySelectorAll('#resultList > *')).map(e=>{const a=e.querySelector('h5 a');return a?{title:a.innerText.trim(),url:a.href,metadata:e.querySelector('.author')?.innerText.trim()||''}:null}).filter(Boolean)}));
 return {source:'国别区域与全球治理数据平台',query,page:1,...data,note:'资源检索首屏，含文章、图书、图表等；非统计数值接口；全文权限未验证。'};
}
