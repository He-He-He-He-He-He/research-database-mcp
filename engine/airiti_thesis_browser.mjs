/* 华艺学位论文：强制切换分类并验证首屏标签；不下载全文。 */
export async function airitiThesisSearch(tab,keyword){
 if(typeof keyword!=='string'||!keyword.trim()||keyword.length>100)throw Error('关键词需为 1–100 字');
 const q=keyword.trim();await tab.goto('https://www.airitilibrary.cn/');
 await tab.playwright.getByRole('textbox',{name:'输入文字、检索符号、ISSN、DOI'}).fill(q);await tab.playwright.getByRole('button',{name:'',exact:true}).click();
 const category=tab.playwright.locator('#Result_種類切換 li[key="學位論文"]');
 try{await category.waitFor({state:'visible',timeoutMs:15000});if(!(await category.getAttribute('class')||'').includes('sliderBtn-active'))await category.click();await tab.playwright.locator('#Result_種類切換 li.sliderBtn-active[key="學位論文"]').waitFor({state:'visible',timeoutMs:15000});await tab.playwright.locator('.col_academicPresent h3 a').first().waitFor({state:'visible',timeoutMs:15000});}catch{throw Error('学位论文分类未就绪；可能无结果、登录或页面变化。');}
 const data=await tab.playwright.evaluate(()=>({active:!!document.querySelector('#Result_種類切換 li.sliderBtn-active[key="學位論文"]'),institution:document.body.innerText.includes('你好!浙江大学')?'浙江大学':null,items:[...document.querySelectorAll('.col_academicPresent')].filter(e=>e.getClientRects().length).map(e=>({title:e.querySelector('h3 a')?.innerText.trim(),id:e.querySelector('input.Result_選擇')?.getAttribute('key'),type:[...e.querySelectorAll('.preTag')].map(x=>x.innerText.trim()),authors:e.querySelector('.author')?.innerText.trim(),source:e.querySelector('.source')?.innerText.trim()})).filter(x=>x.title)}));
 if(!data.active||!data.items.length||data.items.some(i=>!i.type.includes('学位论文')))throw Error('学位类别或结果标签未通过核对，停止读取');
 return {source:'华艺台湾学位论文库',query:q,page:1,...data,note:'仅当前页学位论文题录；页面身份不保证每项全文权限。'};
}
