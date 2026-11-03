/* 近代中日关系文献平台：读取单页简要题录，不复制目录或全文。 */
export async function modernHistorySearch(tab,keyword){
 if(typeof keyword!=='string'||!keyword.trim()||keyword.length>100)throw Error('关键词需为 1–100 字');
 const url='https://www.modernhistory.org.cn/#/SearchResult_list?searchValue='+encodeURIComponent(keyword.trim())+'&seniorType=&selectType=';
 await tab.goto(url);
 try{await tab.playwright.locator('.desc h5').first().waitFor({state:'visible',timeoutMs:15000});}catch(_){throw Error('未读取题录，请检查无结果、登录、验证或页面变化。');}
 const items=await tab.playwright.evaluate(()=>[...document.querySelectorAll('.desc')].slice(0,20).map(e=>({title:e.querySelector('h5')?.textContent.trim(),metadata:[...e.querySelectorAll('td')].filter(c=>!c.querySelector('[role="tree"]')&&!c.innerText.trim().startsWith('目录：')).map(c=>c.innerText.trim()).filter(Boolean)})).filter(e=>e.title));
 return {source:'抗日战争与近代中日关系文献数据平台',query:keyword.trim(),page:1,url,institution:null,items,note:'当前页简要题录；未显示机构身份，全文权限未验证。'};
}
