/** 天禄云枢一般检索首屏书目元数据。 */
export async function tianluSearch(tab,keyword){
 if(typeof keyword!=='string'||!keyword.trim()||keyword.length>100) throw Error('关键词须为 1–100 字');
 const query=keyword.trim();
 await tab.goto('https://tlgj.bbtpress.com/#/');
 const field=tab.playwright.getByPlaceholder('请输入关键词进行检索 多个关键词之间用空格隔开');
 await field.fill(query); await field.press('Enter');
 for(let i=0;i<3;i++){try{await tab.playwright.locator('[id^="el-collapse-head-"] .head-title').first().waitFor({state:'visible',timeoutMs:20000});break;}catch(e){if(i===2)throw e;}}
 const data=await tab.playwright.evaluate(()=>({institution:document.body.innerText.includes('机构名称:浙江大学')?'浙江大学':null,items:Array.from(document.querySelectorAll('[id^="el-collapse-head-"] .head-title')).map(e=>{const lines=e.innerText.split('\n').map(s=>s.trim()).filter(Boolean);return {titleAndMatches:lines[0]||'',classification:lines[1]||'',responsibility:lines[2]||''}})}));
 return {source:'天禄云枢古籍数据库',query,page:1,...data,note:'一般检索首屏书目元数据；未读取正文或验证全文权限。'};
}
