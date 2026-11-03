/** 鼎秀古籍全库搜索首屏题录。 */
export async function dingxiuSearch(tab,keyword){
 if(typeof keyword!=='string'||!keyword.trim()||keyword.length>100) throw Error('关键词须为 1–100 字');
 const query=keyword.trim();
 await tab.goto('https://www.ding-xiu.com/ancientbook/portal/index/index.do');
 const ax=await tab.getAXState({disableDiffing:true,emit:false});
 const index=Number(ax.match(/(\d+) text field[^\n]*ID: searchWord/)?.[1]);
 if(!Number.isInteger(index)) throw Error('未找到搜索框');
 await tab.click(index); await tab.pressKey(null,'super+a'); await tab.typeText(null,query); await tab.pressKey(null,'Return');
 try {await tab.playwright.locator('#tablelist tr td').first().waitFor({state:'visible',timeoutMs:20000});} catch(e) { /* 页面加载后仍需由下方题录检查确认 */ }
 const data=await tab.playwright.evaluate(()=>({institution:document.querySelector('#nologin')?.innerText.includes('浙江大学')?'浙江大学':null,items:Array.from(document.querySelectorAll('#tablelist tr')).map(r=>{const c=Array.from(r.querySelectorAll('td')).map(e=>e.innerText.trim());return c.length>=6?{record:c[1],dynasty:c[2],edition:c[3]}:null}).filter(Boolean)}));
 if(!data.items.length) throw Error('未读取到题录，可能无结果或加载失败');
 return {source:'鼎秀古籍全文检索平台',query,page:1,...data,note:'仅元数据；未读取正文或验证阅读权限。搜索零结果或加载故障可能超时。'};
}
