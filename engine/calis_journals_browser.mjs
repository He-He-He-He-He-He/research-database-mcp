/** CALIS 外文期刊网当前页题录；不请求文献传递或全文。 */
export async function calisJournalsSearch(tab,query){
 if(typeof query!=='string'||!query.trim()||query.length>200)throw Error('关键词不能为空且不得超过200字符');
 await tab.goto('https://ccc2.calis.edu.cn/ccc/index?from=link');
 await tab.playwright.getByPlaceholder('请输入篇名、作者、刊名等').fill(query.trim());
 await tab.playwright.getByRole('button',{name:'检 索'}).click();
 await tab.playwright.locator('table.el-table__body .list-container .title-text').first().waitFor({state:'visible',timeoutMs:30000});
 return await tab.playwright.evaluate(()=>({source:'CALIS外文期刊网',institution:null,items:[...document.querySelectorAll('table.el-table__body .list-container')].filter(e=>e.getClientRects().length).map(e=>({title:e.querySelector('.title-text')?.innerText.trim()||null,authors:e.querySelector('.other-author')?.innerText.trim()||null,journal:e.querySelector('.other-journal .word-blue')?.innerText.trim()||null,citation:e.querySelector('.other-other')?.innerText.trim()||null})).filter(x=>x.title),note:'只读当前页题录；未提交文献传递，未验证浙大身份与全文。检索可能限定返回前2000项。'}));
}
