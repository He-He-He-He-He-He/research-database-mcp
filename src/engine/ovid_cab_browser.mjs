/* 需要用户已在 Ovid 会话中选择 CAB Abstracts + Full Text 的工作标签。 */
export async function ovidCabSearch(tab,keyword){
 if(typeof keyword!=='string'||!keyword.trim()||keyword.length>100)throw Error('关键词需为 1–100 字'); const q=keyword.trim();
 let selected=await tab.playwright.evaluate(()=>document.querySelector('#ovid-resources-link-block')?.innerText.trim()||'');
 if(selected!=='CAB Abstracts + Full Text')throw Error('请先在 Ovid 选择唯一资源 CAB Abstracts + Full Text');
 await tab.playwright.locator('#easy_focus').fill(q);await tab.playwright.locator('#main-search-button').click();
 for(let k=0;k<15;k++){try{await tab.playwright.locator('#searchaid-explain').getByText(q,{exact:false}).first().waitFor({state:'visible',timeoutMs:3000});break;}catch(e){if(k===14)throw e;}}
 await tab.playwright.locator('#titles-records .titles-row .article-title a').first().waitFor({state:'visible',timeoutMs:30000});
 const d=await tab.playwright.evaluate(()=>({selected:document.querySelector('#ovid-resources-link-block')?.innerText.trim(),searchInfo:document.querySelector('#searchaid-explain')?.innerText.trim(),items:[...document.querySelectorAll('#titles-records .titles-row')].filter(e=>e.getClientRects().length).map(e=>({title:e.querySelector('.article-title a')?.innerText.trim(),author:e.querySelector('.article-authors')?.innerText.trim(),source:e.querySelector('.article-source')?.innerText.trim(),type:e.querySelector('.article-pubtype')?.innerText.trim()})).filter(x=>x.title)}));
 if(d.selected!=='CAB Abstracts + Full Text'||!d.searchInfo?.includes(q)||!d.items.length)throw Error('资源或当前检索未确认');return {source:'CAB Abstracts + Full Text via Ovid',query:q,...d,note:'Ovid 基本检索默认包含相关词；当前页题录，不读取摘要或全文。'};
}
