/** Read current metadata from two publisher-documented RUP RSS feeds. */
const FEEDS={jcb:'https://rupress.org/rss/site_1000001/LatestArticles_1000003.xml',jgp:'https://rupress.org/rss/site_1000005/LatestArticles_1000005.xml'};
export async function rupRss(tab,feed='jcb',keyword='',limit=10){
 if(!Object.hasOwn(FEEDS,feed))throw Error('unsupported RUP feed');
 if(typeof keyword!=='string'||keyword.length>100)throw Error('keyword must be at most 100 characters');
 if(!Number.isInteger(limit)||limit<1||limit>20)throw Error('limit must be 1–20');
 await tab.goto(FEEDS[feed]);
 const d=await tab.playwright.evaluate(({keyword,limit})=>{
  const u=new URL(location.href),txt=(e,s)=>e.querySelector(s)?.textContent?.trim()||null;
  const all=[...document.querySelectorAll('item')].map(e=>({title:txt(e,'title'),url:txt(e,'link'),date:txt(e,'pubDate')}));
  const found=all.filter(e=>e.title?.toLocaleLowerCase().includes(keyword.toLocaleLowerCase()));
  return {host:u.hostname,path:u.pathname,type:document.contentType,feed:txt(document,'channel > title'),total:all.length,matches:found.length,items:found.slice(0,limit)};
 },{keyword,limit});
 const expected=new URL(FEEDS[feed]);
 if(d.host!==expected.hostname||d.path!==expected.pathname||!['application/rss+xml','application/xml','text/xml'].includes(d.type)||!d.feed)throw Error('RUP RSS response unavailable or unexpected');
 return {source:'Rockefeller University Press official RSS',feed_name:d.feed,keyword,total_in_feed:d.total,matches_in_feed:d.matches,items:d.items,note:'当前 RSS 源标题本地筛选；非全文、完整期刊库、历史检索或机构授权证明。'};
}
