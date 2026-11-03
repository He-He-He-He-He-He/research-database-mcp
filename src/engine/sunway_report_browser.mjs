/** 尚唯科技报告：按报告名称搜索，读取结果首屏元数据。 */
export async function sunwayReportSearch(tab,keyword){
 if(typeof keyword!=='string'||!keyword.trim()||keyword.trim().length>100) throw Error('关键词须为 1–100 个字符');
 const query=keyword.trim(); await tab.goto('https://bg.sunwayinfo.com.cn/');
 await tab.playwright.getByPlaceholder('请输入检索关键词').fill(query); await tab.playwright.getByRole('button',{name:'开始检索'}).click();
 await tab.playwright.locator('.box .title_txt').first().waitFor({state:'visible',timeoutMs:20000});
 const data=await tab.playwright.evaluate(()=>({institution:document.body.innerText.includes('浙江大学 欢迎访问')?'浙江大学':null,items:Array.from(document.querySelectorAll('.box')).filter(e=>e.querySelector('.title_txt')).map(e=>({title:e.querySelector('.title_txt')?.innerText.trim()||'',titleOriginal:e.querySelector('.title_txt')?.getAttribute('title')||'',reportNumber:e.querySelector('.tr1_left div:nth-child(2)')?.innerText.trim()||'',date:e.querySelector('.pub_date span')?.innerText.trim()||'',authors:Array.from(e.querySelectorAll('.content_table tr:nth-child(2) td:nth-child(2) span')).map(x=>x.innerText.trim()).filter(Boolean)}))}));
 return {source:'尚唯科技报告资源服务系统',query,page:1,...data,note:'报告名称搜索当前页；全文未验证，无结果或页面变化可能超时。'};
}
