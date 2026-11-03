/* 北大法宝中央法规标题检索，读取默认分组展示的首屏。 */
export async function pkulawSearch(tab,keyword){
 if(typeof keyword!=='string'||!keyword.trim()||keyword.length>100)throw Error('关键词需为 1–100 字');
 const u=new URL('https://www.pkulaw.com/law/chl');u.search=new URLSearchParams({Keywords:keyword.trim(),SearchKeywordType:'Title',MatchType:'Exact'}).toString();await tab.goto(u.toString());await tab.getAXState({emit:false});
 const data=await tab.playwright.evaluate(()=>({items:[...document.querySelectorAll('.t h4 a[href^="/chl/"]')].map(a=>({title:a.innerText.trim(),url:a.href,id:a.closest('.t')?.querySelector('input[name="recordList"]')?.value})).filter(x=>x.title)}));
 if(!data.items.length)throw Error('没有读取到结果；可能无结果、登录、验证码或网页变化。');
 return {source:'北大法宝',query:keyword.trim(),scope:'中央法规标题精确检索，默认分组视图中的当前可见条目，并非完整结果',institution:null,...data,note:'机构识别和全文权限未确认；不得推断全部结果。'};
}
