/* 民国文献大全：标题检索后读取图书首屏目录，不阅读原图。 */
export async function minguoBookSearch(tab,keyword){
 if(typeof keyword!=='string'||!keyword.trim()||keyword.length>100)throw Error('关键词需为 1–100 字');
 await tab.goto('https://cadal.hytung.com.cn/');
 await tab.playwright.locator('#ddlField').selectOption({label:'標題'});
 await tab.playwright.locator('#txtKeyword').fill(keyword.trim());
 await tab.playwright.locator('#BtnExact').click();
 try{await tab.playwright.locator('#bR a.book').first().waitFor({state:'visible',timeoutMs:15000});await tab.playwright.locator('#bR a.book').first().click();await tab.playwright.locator('#DataList .srcell').first().waitFor({state:'visible',timeoutMs:15000});}catch(_){throw Error('未读取图书题录，请检查无结果、机构权限或页面变化。');}
 const data=await tab.playwright.evaluate(()=>({institution:document.querySelector('#pIPLogout')?.innerText.includes('浙江大学')?'浙江大学':null,items:[...document.querySelectorAll('#DataList .srcell')].map(e=>({source:e.querySelector('.derivation')?.innerText.trim(),title:e.querySelector('.ctitle')?.innerText.trim()})).filter(x=>x.title)}));
 return {source:'民国文献大全',query:keyword.trim(),page:1,...data,note:'图书标题检索首屏，结果可能为同书不同章节；机构与图像权限因资源而异。'};
}
