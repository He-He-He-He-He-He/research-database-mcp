/** CALIS e读学术资源发现：只读当前页题录。 */
export async function calisYiduSearch(tab,query){
 if(typeof query!=='string'||!query.trim()||query.length>200)throw Error('关键词不能为空且不得超过200字符');
 await tab.goto('https://yidu.calis.edu.cn/');
 await tab.playwright.getByPlaceholder('输入关键词').fill(query.trim());
 await tab.playwright.getByRole('button',{name:'检 索'}).click();
 await tab.playwright.locator('table.el-table__body .list-container .title-text').first().waitFor({state:'visible',timeoutMs:30000});
 const data=await tab.playwright.evaluate(()=>({source:'CALIS e读学术资源发现',institution:null,items:[...document.querySelectorAll('table.el-table__body .list-container')].filter(e=>e.getClientRects().length).map(e=>({title:e.querySelector('.title-text')?.innerText.trim()||null,type:e.querySelector('.list-category')?.innerText.trim()||null,authors:e.querySelector('.other-author')?.innerText.trim()||null,publication:e.querySelector('.other-journal')?.innerText.trim()||null,citation:e.querySelector('.other')?.innerText.trim()||null})).filter(x=>x.title),note:'当前页跨库题录，不提交文献传递；未确认浙大身份与全文权限。网站可能仅返回前2000条。'}));
 if(!data.items.length)throw Error('未取得题录，请检查页面');return data;
}
