/** 域外汉籍库当前页题录，使用 CUA 已绑定 Tab。 */
export async function overseasHanSearch(tab,keyword){
 if(typeof keyword!=='string'||!keyword.trim()||keyword.length>100) throw Error('关键词须为 1–100 字');
 const query=keyword.trim();
 await tab.goto('https://gj.reasonlib.com/');
 await tab.playwright.locator('#searchval').fill(query);
 await tab.playwright.locator('#SearchBtn').click();
 for(let i=0;i<3;i++){try{await tab.playwright.locator('#advItem .list-item').first().waitFor({state:'visible',timeoutMs:20000});break;}catch(e){if(i===2)throw e;}}
 const data=await tab.playwright.evaluate(()=>({institution:document.querySelector('#loginshow')?.innerText.includes('浙江大学')?'浙江大学（试用户）':null,items:Array.from(document.querySelectorAll('#advItem .list-item')).map(e=>{const a=Array.from(e.querySelectorAll('a')).find(a=>a.innerText.trim()&&a.innerText.trim()!=='更多信息');const lines=e.innerText.split('\n').map(x=>x.trim()).filter(Boolean);return a?{title:a.innerText.trim(),edition:lines[1]||'',url:a.href}:null}).filter(Boolean)}));
 return {source:'域外汉籍库',query,page:1,...data,note:'仅首屏题录，试用状态及影像阅读权限可能变化。'};
}
