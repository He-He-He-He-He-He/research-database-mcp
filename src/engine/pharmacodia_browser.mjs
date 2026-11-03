/** 药渡数据公开搜索预览；不登录、只读取当前展示的药物卡片。 */
export async function pharmacodiaSearch(tab,keyword) {
 if(typeof keyword!=='string'||!keyword.trim()||keyword.trim().length>100) throw Error('关键词须为 1–100 个字符');
 const query=keyword.trim();
 await tab.goto('https://data.pharmacodia.com/');
 const input=tab.playwright.getByPlaceholder('药品名称/靶点/公司/适应症');
 await input.fill(query); await input.press('Enter');
 await tab.playwright.getByRole('button',{name:'搜索'}).click();
 await tab.playwright.locator('.information-card .card-item').first().waitFor({state:'visible',timeoutMs:20000});
 const items=await tab.playwright.evaluate(()=>Array.from(document.querySelectorAll('.information-card .card-item')).map(e=>({name:e.querySelector('.name .cn')?.innerText.trim()||'',englishName:e.querySelector('.name .en')?.innerText.trim()||'',fields:Array.from(e.querySelectorAll('.content .flex')).map(x=>({label:x.querySelector('.key')?.innerText.trim()||'',value:x.querySelector('.val')?.innerText.trim()||'',additional:x.querySelector('.num')?.innerText.trim()||''})).filter(x=>x.label)})).filter(x=>x.name||x.englishName));
 return {source:'药渡数据',query,institution:null,items,note:'公开搜索预览，完整数据提示登录；字段可能截断，不能用于医疗决策。'};
}
