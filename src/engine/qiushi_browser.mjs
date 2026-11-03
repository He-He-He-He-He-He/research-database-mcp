/* 浙江大学求是学术搜索：只读取首屏题录，不获取全文。 */
export async function qiushiSearch(tab,keyword){
 if(typeof keyword!=='string'||!keyword.trim()||keyword.length>100)throw Error('关键词需为 1–100 字');
 const q=keyword.trim(),params=new URLSearchParams({pn:'1',ho:'t','include.ft.matches':'f',l:'zh-CN',q});
 await tab.goto('about:blank');
 await tab.goto('https://zju.summon.serialssolutions.com/#!/search?'+params.toString());
 try{await tab.playwright.locator('#results .documentSummary h3').first().waitFor({state:'visible',timeoutMs:20000});}catch{throw Error('未读取题录；可能无结果、验证、网络或页面变化，请查看网页。');}
 const items=await tab.playwright.evaluate(()=>[...document.querySelectorAll('#results .documentSummary')].filter(e=>e.getClientRects().length).map(e=>({title:e.querySelector('.title h3')?.innerText.trim(),authors:e.querySelector('.authors')?.innerText.trim().replace(/^著者\s*/,'')||null,publication:e.querySelector('.summary')?.innerText.trim()||null,url:e.querySelector('.title h3 a[href]')?.href||null})).filter(x=>x.title));
 if(!items.length)throw Error('未读取当前页题录');
 return {source:'浙江大学求是学术搜索',query:q,page:1,items,note:'本馆专属搜索入口，返回当前页聚合题录；显示在线全文不保证实际授权，未读取全文。'};
}
