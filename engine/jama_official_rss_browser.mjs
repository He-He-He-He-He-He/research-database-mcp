/** Read the current items in two publisher-documented JAMA RSS feeds. */
const FEEDS={jama_current:'https://jamanetwork.com/rss/site_3/67.xml',jama_network_open:'https://jamanetwork.com/rss/site_214/187.xml'};
export async function jamaRss(tab,feed='jama_current',keyword='',limit=10){
 if(!Object.hasOwn(FEEDS,feed))throw Error('unsupported JAMA feed');
 if(typeof keyword!=='string'||keyword.length>100)throw Error('keyword must be at most 100 characters');
 if(!Number.isInteger(limit)||limit<1||limit>20)throw Error('limit must be 1–20');
 await tab.goto(FEEDS[feed]);
 const d=await tab.playwright.evaluate(({keyword,limit})=>{
  let u=new URL(location.href),txt=(e,s)=>e.querySelector(s)?.textContent?.trim()||null;
  const all=[...document.querySelectorAll('item')].map(e=>({title:txt(e,'title'),url:txt(e,'link'),date:txt(e,'pubDate')}));
  const filtered=all.filter(e=>e.title?.toLocaleLowerCase().includes(keyword.toLocaleLowerCase()));
  return {host:u.hostname,path:u.pathname,type:document.contentType,feed:txt(document,'channel > title'),total:all.length,matches:filtered.length,items:filtered.slice(0,limit)};
 },{keyword,limit});
 const expected=new URL(FEEDS[feed]);
 if(d.host!==expected.hostname||d.path!==expected.pathname||!['application/rss+xml','application/xml','text/xml'].includes(d.type)||!d.feed)throw Error('JAMA RSS unavailable or returned an unexpected page');
 return {source:'JAMA Network official RSS',feed_name:d.feed,keyword,total_in_feed:d.total,matches_in_feed:d.matches,items:d.items,note:'当前订阅源内本地标题筛选，可能包含非研究文章；不是全库检索，非机构订购或全文权限证明。'};
}
