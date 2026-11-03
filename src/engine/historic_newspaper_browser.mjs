/** 全国报刊索引中国近代报纸首屏题录。 */
export async function historicNewspaperSearch(tab,keyword){
 if(typeof keyword!=='string'||!keyword.trim()||keyword.length>100) throw Error('关键词须为 1–100 个字符');
 const query=keyword.trim();
 await tab.goto('https://www.cnbksy.com/search/advance?pid=22&isProduct=false');
 for(let i=0;i<3;i++){try {await tab.playwright.locator('#productTree_144_check.checkbox_true_full').waitFor({state:'attached',timeoutMs:20000}); break;} catch(e){if(i===2) throw e;}}
 await tab.playwright.locator('#productTree_144_check').click();
 await tab.playwright.locator('#productTree_27_check').click();
 const scope=await tab.playwright.evaluate(()=>({news:document.querySelector('#productTree_27_check')?.className,other:document.querySelector('#productTree_144_check')?.className}));
 if(!scope.news?.includes('checkbox_true_full')||!scope.other?.includes('checkbox_false_full')) throw Error('报纸子库筛选状态未确认');
 await tab.playwright.locator('#sf_1 input.advSearch').first().fill(query);
 await tab.playwright.getByRole('link',{name:'检 索',exact:true}).click();
 for(let i=0;i<4;i++){try {await tab.playwright.locator('#rt_1 a[href*="/search/detail/"]').first().waitFor({state:'visible',timeoutMs:20000}); break;} catch(e){if(i===3) throw e;}}
 const data=await tab.playwright.evaluate(()=>({institution:document.body.innerText.includes('[浙江大学图书馆]')?'浙江大学图书馆':null,items:Array.from(document.querySelectorAll('#rt_1 table')).map(e=>{const a=e.querySelector('a[href*="/search/detail/"]');return a?{title:a.innerText.trim(),url:a.href,metadata:e.innerText.replace(a.innerText,'').split('整本浏览')[0].trim()}:null}).filter(Boolean)}));
 return {source:'中国近代报纸全文数据库',query,page:1,...data,note:'仅首屏题录，机构识别不代表全文权限；无结果或加载故障可能超时。'};
}
