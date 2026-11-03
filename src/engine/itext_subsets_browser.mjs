/** 爱教材 Wiley/CRC 子库首页书目；不提供跨页搜索或正文。 */
async function browse(tab,product,id){
 await tab.goto('https://www.itextbook.cn/f/db/officeDbDetail?'+new URLSearchParams({connDbId:id}));
 await tab.playwright.locator('.book-info p.title a').first().waitFor({state:'visible',timeoutMs:20000});
 const d=await tab.playwright.evaluate(()=>({institution:document.body.innerText.includes('浙江大学 IP读者')?'浙江大学':null,items:[...document.querySelectorAll('.book-info')].filter(x=>x.getClientRects().length).map(x=>{let a=x.querySelector('p.title a');return {title:a?.innerText.trim()||null,url:a?.href||null,authors:x.querySelector('.start-group')?.innerText.trim()||null,metadata:x.querySelector('p.text:last-of-type')?.innerText.trim()||null}}).filter(x=>x.title)}));
 if(!d.institution||!d.items.length)throw Error('未确认机构或书目');
 return {source:'爱教材 '+product+' 子库',...d,note:'仅子库当前首页书目；忽略传入关键词，不是搜索或全量清单；已购标签与个别全文权限未逐项核验。'};
}
export const itextWileyBrowse=tab=>browse(tab,'Wiley','f0c99a89ee5f4852b4c996a65eefa88e');
export const itextCrcBrowse=tab=>browse(tab,'CRC','75fcf6f226454e898939e13a58b77d63');
