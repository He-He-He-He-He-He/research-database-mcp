/** 国外学位论文中国集团全文检索平台，当前页题录。 */
export async function pqdtChinaSearch(tab,query){
 if(typeof query!=='string'||!query.trim()||query.length>300)throw Error('关键词不能为空且不得超过 300 字符');
 await tab.goto('https://www.pqdtcn.com/');
 await tab.playwright.locator('#to_retrieve').fill(query.trim());
 await tab.playwright.locator('#index-search-bt').click();
 await tab.playwright.locator('a[href^="/thesisDetails/"]').first().waitFor({state:'visible',timeoutMs:30000});
 return await tab.playwright.evaluate(()=>({source:'国外学位论文中国集团全文检索平台',institution:document.body.innerText.match(/当前IP所处机构\s*[:：]\s*[^\n]+/)?.[0]||null,items:[...document.querySelectorAll('table.table')].filter(x=>x.getClientRects().length).map(x=>{let a=x.querySelector('a[href^="/thesisDetails/"]');return {title:a?.innerText.trim()||null,url:a?.href||null,citation:x.querySelector('td.col-md-10')?.innerText.trim()||null,access_label:x.querySelector('img[id^="orbuy"]')?.getAttribute('title')||null}}).filter(x=>x.title&&x.url),note:'仅当前页题录，逐条标签表示网站显示的订购状态，未下载或验证全文。'}));
}
