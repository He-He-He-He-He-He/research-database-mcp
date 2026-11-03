/** 尚古汇典第五期：普通检索后强制勾选第五期，仅返回首屏出处元数据。 */
export async function gujidhFifthSearch(tab,keyword){
 if(typeof keyword!=='string'||!keyword.trim()||keyword.trim().length>100)throw Error('关键词须为 1–100 字');
 const query=keyword.trim();
 await tab.goto('https://www.gujidh.com/library-normal/'+encodeURIComponent(query)+'/100013122/'+encodeURIComponent('典籍整理文献数据库')+'/content');
 const title=tab.playwright.locator('.ant-tree-title').filter({hasText:'第五期'}).first();
 try{await title.waitFor({state:'visible',timeoutMs:20000});}catch{throw Error('未见第五期筛选项；可能无匹配、需登录或页面变化。');}
 const label=await title.innerText();const match=label.match(/^第五期\s*[（(]\s*([\d,]+)\s*[）)]$/);if(!match)throw Error('第五期数量无法确认，停止读取');
 const expected=Number(match[1].replace(/,/g,''));if(!expected)throw Error('第五期无匹配结果');if(expected>=10000)throw Error('第五期筛选数达到网站结果上限，无法核对加载状态；请缩小检索范围');
 const before=Number((await tab.playwright.locator('.search-record .total').innerText()).replace(/[,\s]/g,''));if(before===expected)throw Error('筛选前后数量相同，无法确认结果刷新；请在网页核对');
 const node=tab.playwright.locator('.ant-tree-treenode').filter({hasText:label}).first();await node.locator('.ant-tree-checkbox',{}).click();
 try{await tab.playwright.locator('.search-record .total').filter({hasText:String(expected)}).first().waitFor({state:'visible',timeoutMs:20000});await tab.playwright.locator('.items').filter({hasText:'结果出处：'}).first().waitFor({state:'visible',timeoutMs:20000});}catch{throw Error('第五期筛选结果未加载完成或页面变化');}
 const data=await tab.playwright.evaluate(()=>{const tree=[...document.querySelectorAll('.ant-tree-treenode')].find(e=>/^第五期\s*[（(]/.test(e.querySelector('.ant-tree-title')?.innerText||''));const total=Number((document.querySelector('.search-record .total')?.innerText||'').replace(/[,\s]/g,''));return {selected:!!tree?.querySelector('.ant-tree-checkbox-checked'),total,institution:/所在机构：\s*浙江大学/.test(document.body.innerText)?'浙江大学':null,results:[...document.querySelectorAll('.items')].filter(e=>e.getClientRects().length&&e.innerText.trim().startsWith('结果出处：')).map(e=>{const rows=[...e.parentElement.children].filter(x=>x.classList.contains('items')).map(x=>x.innerText.trim());const value=k=>(rows.find(x=>x.startsWith(k))||'').slice(k.length).trim();return {source:value('结果出处：'),responsibility:value('责任者：'),publication:value('出版信息：')}})}});
 if(!data.selected||data.total!==expected||!data.results.length)throw Error('第五期勾选或结果数量未通过核对，停止读取');
 return {database:'尚古汇典·典籍整理文献数据库（第五期）',query,searchType:'正文匹配',page:1,...data,note:'第五期筛选首屏出处元数据；机构识别不代表每本全文授权，未读取全文。'};
}
