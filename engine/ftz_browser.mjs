/** 全国报刊索引“一带一路”专题首屏题录。 */
export async function ftzSearch(tab,keyword){
 if(typeof keyword!=='string'||!keyword.trim()||keyword.length>100) throw Error('关键词须为 1–100 个字符');
 const query=keyword.trim();
 await tab.goto('https://www.cnbksy.com/search/advance?pid=21&isProduct=false');
 for(let i=0;i<3;i++){try {await tab.playwright.locator('#productTree_146_check.checkbox_true_full').waitFor({state:'attached',timeoutMs:20000}); break;} catch(e){if(i===2) throw e;}}
 await tab.playwright.locator('#sf_1 input.advSearch').first().fill(query);
 await tab.playwright.getByRole('link',{name:'检 索',exact:true}).click();
 for(let i=0;i<4;i++){try {await tab.playwright.locator('#rt_1 a[href*="/search/detail/"]').first().waitFor({state:'visible',timeoutMs:20000}); break;} catch(e){if(i===3) throw e;}}
 const data=await tab.playwright.evaluate(()=>({institution:document.body.innerText.includes('[浙江大学图书馆]')?'浙江大学图书馆':null,items:Array.from(document.querySelectorAll('#rt_1 table')).map(e=>{const a=e.querySelector('a[href*="/search/detail/"]');return a?{title:a.innerText.trim(),url:a.href,metadata:e.innerText.replace(a.innerText,'').trim()}:null}).filter(Boolean)}));
 return {source:'全国报刊索引自由贸易试验区建设专题数据库',query,page:1,...data,note:'仅首屏题录，机构识别不代表全文权限；无结果或加载故障可能超时。'};
}
