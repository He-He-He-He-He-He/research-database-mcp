/** Cochrane Library 默认综述搜索的当前页题录，不抓取摘要或全文。 */
export async function cochraneReviewsSearch(tab, query) {
 if(typeof query!=='string'||!query.trim()||query.length>300) throw Error('关键词不能为空且不得超过 300 字符');
 const p=new URLSearchParams({p_p_id:'scolarissearchresultsportlet_WAR_scolarissearchresults',p_p_lifecycle:'0',_scolarissearchresultsportlet_WAR_scolarissearchresults_searchType:'basic',_scolarissearchresultsportlet_WAR_scolarissearchresults_searchBy:'1',_scolarissearchresultsportlet_WAR_scolarissearchresults_searchText:query.trim()});
 try { await tab.goto('https://www.cochranelibrary.com/search?'+p); } catch (e) { if(!String(e).includes('Timed out waiting for tab')) throw e; }
 await tab.playwright.locator('.search-results-item-body').first().waitFor({state:'visible',timeoutMs:25000});
 const current=await tab.playwright.evaluate(()=>document.querySelector('#searchText')?.value||'');
 if(current!==query.trim()) throw Error('搜索页面尚未更新到指定关键词');
 return await tab.playwright.evaluate(()=>({source:'Cochrane Library',scope:'默认综述结果，当前页',institution:null,items:[...document.querySelectorAll('.search-results-item-body')].filter(x=>x.getClientRects().length).map(x=>{const a=x.querySelector('h3 a');return {title:a?.innerText.trim()||null,url:a?.href||null,authors:x.querySelector('.search-result-authors')?.innerText.trim()||null,type:x.querySelector('.search-result-type')?.innerText.trim()||null,stage:x.querySelector('.search-result-stage')?.innerText.trim()||null,date:x.querySelector('.search-result-date')?.innerText.trim()||null}}).filter(x=>x.title&&x.url),note:'未验证机构身份、单篇全文或试验数据库；链接指向全文页面不代表具有全文权限。'}));
}
