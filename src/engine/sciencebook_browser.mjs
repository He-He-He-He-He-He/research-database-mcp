/** 科学文库单页题录，使用 CUA 已绑定 Tab。 */
export async function scienceBookSearch(tab,keyword){
 if(typeof keyword!=='string'||!keyword.trim()||keyword.length>100) throw Error('关键词须为 1–100 个字符');
 const query=keyword.trim();
 await tab.goto('https://book.sciencereading.cn/shop/main/Login/shopFrame.do');
 await tab.playwright.getByPlaceholder('在全库检索').fill(query);
 try { await tab.playwright.getByRole('button',{name:'搜索',exact:true}).click(); } catch(e) { /* 页面提交有时因导航等待超时，下面仍校验结果 */ }
 for(let i=0;i<3;i++){try{await tab.playwright.locator('.book_detail_title a[href*="Booksimple/show.do?id="]').first().waitFor({state:'visible',timeoutMs:20000});break;}catch(e){if(i===2)throw e;}}
 const data=await tab.playwright.evaluate(()=>({institution:document.body.innerText.includes('浙江大学 您好')?'浙江大学':null,items:Array.from(document.querySelectorAll('.book_detail_title a[href*="Booksimple/show.do?id="]')).map(a=>{
  const card=a.parentElement.parentElement.parentElement; const text=card.innerText; const field=label=>text.match(new RegExp(label+'：\\s*([^\\n]+)'))?.[1]?.trim()||'';
  return {title:a.innerText.trim(),url:a.href,author:field('作者'),isbn:field('ISBN'),publisher:field('出版社'),date:field('出版日期')};
 }).filter(x=>x.title)}));
 return {source:'科学文库',query,page:1,...data,note:'单页题录；页面识别机构，全文权限未验证；无结果或页面变化可能超时。'};
}
