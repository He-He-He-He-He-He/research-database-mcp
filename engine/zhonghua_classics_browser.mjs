/* 中华经典古籍库图书题录：仅首页，不读取加密正文。 */
export async function zhonghuaClassicsSearch(tab,keyword){
 if(typeof keyword!=='string'||!keyword.trim()||keyword.length>100)throw Error('关键词需为 1–100 字');
 const q=keyword.trim(),u=new URL('https://jingdian.ancientbooks.cn/6/search');u.search=new URLSearchParams({txt:q,useSynonyms:''}).toString();await tab.goto(u.toString());
 await tab.playwright.getByText('图书结果',{exact:true}).click();
 try{await tab.playwright.getByRole('button',{name:'确认',exact:true}).click({timeoutMs:3000});}catch{}
 try{await tab.playwright.locator('form.form-description').first().waitFor({state:'visible',timeoutMs:20000});}catch{throw Error('未读取图书题录，请检查无结果、登录或页面变化。');}
 const data=await tab.playwright.evaluate(()=>({institution:document.body.innerText.includes('浙江大学')?'浙江大学':null,items:[...document.querySelectorAll('form.form-description')].filter(f=>f.getClientRects().length).map(f=>{let p=f.parentElement, fields={};for(let e of f.querySelectorAll('.el-form-item')){let k=e.querySelector('.el-form-item__label')?.innerText.replace(/\s/g,''),v=e.querySelector('.el-form-item__content span[title]')?.getAttribute('title');if(k&&v&&k!=='简介')fields[k]=v;}return {title:p.querySelector('h2')?.innerText.trim(),author:fields['作者']||null,editor:fields['整理者']||null,otherTitle:fields['其他题名']||null,category:fields['分类']||null};}).filter(x=>x.title)}));
 if(!data.items.length)throw Error('未读取图书题录，请检查结果页面。');
 return {source:'中华经典古籍库',query:q,page:1,...data,note:'图书结果当前页元数据；正文使用网站字体编码，不读取正文或全文。'};
}
