/** 全球案例发现系统，读取当前页案例素材题录。 */
export async function htCasesSearch(tab,keyword){
 if(typeof keyword!=='string'||!keyword.trim()||keyword.trim().length>100)throw Error('关键词须为 1–100 个字符');
 const query=keyword.trim();await tab.goto('https://www.htcases.com.cn/v/#/meta/list?queryTxt='+encodeURIComponent(query));
 for(let i=0;i<3;i++){try{await tab.playwright.locator('.details-left .details-title a').first().waitFor({state:'visible',timeoutMs:20000});break;}catch(e){if(i===2)throw Error('未读取案例结果；可能加载缓慢、无结果或页面变化');}}
 const data=await tab.playwright.evaluate(()=>({institution:document.body.innerText.includes('浙江大学')?'浙江大学':null,items:Array.from(document.querySelectorAll('.details-left')).filter(x=>x.getClientRects().length).map(e=>({title:e.querySelector('.details-title a')?.innerText.trim()||'',metadata:Array.from(e.querySelectorAll('.line-no')).map(x=>x.innerText.trim().replace(/^\s*•\s*/,''))})).filter(x=>x.title)}));
 return {source:'全球案例发现系统',query,page:1,...data,note:'当前页案例素材题录；详情与全文权限未验证。'};
}
