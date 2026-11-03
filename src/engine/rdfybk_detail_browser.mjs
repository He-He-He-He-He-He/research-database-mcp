/** 读取人大复印资料已打开的文献详情题录，不读取摘要或正文。 */
export async function rdfybkDetail(tab,id){
 if(typeof id!=='string'||!/^\d{1,20}$/.test(id))throw Error('请输入题录的数字文献 ID');
 const d=await tab.playwright.evaluate(()=>{let u=new URL(location.href);return {host:u.hostname,path:u.pathname,id:u.searchParams.get('id'),institution:[...document.querySelectorAll('button')].some(e=>e.innerText.trim()==='浙江大学'),title:document.querySelector('#artTitles')?.innerText.trim(),translatedTitle:document.querySelector('#subTitleNote')?.innerText.trim()||null,authors:[...document.querySelectorAll('#autInfo a')].map(e=>e.innerText.trim()).filter(Boolean),keywords:[...document.querySelectorAll('#artKeyword a')].map(e=>e.innerText.trim()).filter(Boolean),originalJournal:document.querySelector('#artPdcInfo')?.innerText.replace(/\s+/g,' ').trim()||null}});
 if(d.host!=='www.rdfybk.com'||d.path!=='/qw/detail'||d.id!==id||!d.title||!d.originalJournal)throw Error('文献详情页、编号或出处未确认');return {source:'人大复印报刊资料文献题录',...d,institution:d.institution?'浙江大学':null,note:'已打开页面的书目信息；不读取摘要和正文，机构标识不证明逐篇授权。'};
}
