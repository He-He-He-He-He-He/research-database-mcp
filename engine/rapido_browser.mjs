/** 浙大 RAPIDO 未登录中央索引单页题录，不发起文献请求。 */
export async function rapidoSearch(tab,query){
 if(typeof query!=='string'||!query.trim()||query.length>200||query.includes(','))throw Error('关键词须为1–200字且不含逗号');
 const q=query.trim();let p=new URLSearchParams({query:'any,contains,'+q,tab:'CentralIndex',search_scope:'CentralIndex',vid:'86ZJU_INST:RAPIDO_SA_VIEW',lang:'zh',offset:'0'});
 await tab.goto('https://zju.rapido.exlibrisgroup.com.cn/discovery/search?'+p);
 for(let i=0;i<3;i++){try{await tab.playwright.locator('[id^="SEARCH_RESULT_RECORDID_"] h3 a').first().waitFor({state:'visible',timeoutMs:30000});break;}catch(e){if(i===2)throw e;await tab.getAXState({emit:false});}}
 const d=await tab.playwright.evaluate(()=>({url:location.href,items:[...document.querySelectorAll('[id^="SEARCH_RESULT_RECORDID_"]')].filter(e=>e.getClientRects().length).map(e=>{let a=e.querySelector('h3 a');return {title:a?.innerText.trim()||null,url:a?.href||null,id:e.getAttribute('data-recordid')||null}}).filter(x=>x.title&&x.url)}));
 if(new URL(d.url).searchParams.get('query')!=='any,contains,'+q||!d.items.length)throw Error('未确认查询结果');
 return {source:'浙大 RAPIDO 中央索引',query:q,...d,note:'未登录页面提示登录可获取完整结果并请求资源；仅首屏题录，不发起互借或验证全文。'};
}
