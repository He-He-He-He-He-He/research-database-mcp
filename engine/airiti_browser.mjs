/* 华艺学术文献数据库：普通检索的当前分类首屏。 */
export async function airitiSearch(tab,keyword){
 if(typeof keyword!=='string'||!keyword.trim()||keyword.length>100)throw Error('关键词需为 1–100 字');
 await tab.goto('https://www.airitilibrary.cn/');
 await tab.playwright.getByRole('textbox',{name:'输入文字、检索符号、ISSN、DOI'}).fill(keyword.trim());
 await tab.playwright.getByRole('button',{name:'',exact:true}).click();
 try{await tab.playwright.locator('.col_academicPresent h3 a').first().waitFor({state:'visible',timeoutMs:15000});}catch(_){throw Error('未读取到结果；请检查无结果、登录、验证或网页结构变化。');}

 const data=await tab.playwright.evaluate(()=>({institution:document.body.innerText.includes('你好!浙江大学')?'浙江大学':null,items:[...document.querySelectorAll('.col_academicPresent')].map(e=>({title:e.querySelector('h3 a')?.innerText.trim(),id:e.querySelector('input.Result_選擇')?.getAttribute('key'),type:[...e.querySelectorAll('.preTag')].map(x=>x.innerText.trim()),authors:e.querySelector('.author')?.innerText.trim(),source:e.querySelector('.source')?.innerText.trim(),abstract:e.querySelector('.fullcontext')?.innerText.trim()})).filter(x=>x.title)}));
 if(!data.items.length) throw Error('未读取到结果；请检查无结果、登录、验证或网页结构变化。');
 return {source:'华艺学术文献数据库',query:keyword.trim(),page:1,...data,note:'当前页面选中的资源类别，题录及摘要可能不完整，全文权限未测试。'};
}
