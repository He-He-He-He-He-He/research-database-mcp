/** Current article headlines from two ASCE publisher-documented RSS feeds. */
const FEEDS={construction:'jcemd4',structural:'jsendh'};
export async function asceRss(tab,feed='construction',keyword='',limit=10){
 if(!Object.hasOwn(FEEDS,feed))throw Error('unsupported ASCE feed');
 if(typeof keyword!=='string'||keyword.length>100)throw Error('keyword must be at most 100 characters');
 if(!Number.isInteger(limit)||limit<1||limit>20)throw Error('limit must be 1–20');
 const p=new URLSearchParams({type:'etoc',feed:'rss',jc:FEEDS[feed]});
 await tab.goto('https://ascelibrary.org/action/showFeed?'+p.toString());
 const d=await tab.playwright.evaluate(({keyword,limit})=>{
  const u=new URL(location.href),txt=(e,s)=>e.querySelector(s)?.textContent?.trim()||null;
  const all=[...document.querySelectorAll('item')].map(e=>({title:txt(e,'title'),url:txt(e,'link'),date:txt(e,'date')}));
  const found=all.filter(e=>e.title?.toLocaleLowerCase().includes(keyword.toLocaleLowerCase()));
  return {host:u.hostname,path:u.pathname,code:u.searchParams.get('jc'),type:document.contentType,feed:txt(document,'channel > title'),total:all.length,matches:found.length,items:found.slice(0,limit)};
 },{keyword,limit});
 if(d.host!=='ascelibrary.org'||d.path!=='/action/showFeed'||d.code!==FEEDS[feed]||!['application/rss+xml','application/xml','text/xml'].includes(d.type)||!d.feed)throw Error('ASCE RSS response unavailable or unexpected');
 return {source:'ASCE Library official RSS',feed_name:d.feed,keyword,total_in_feed:d.total,matches_in_feed:d.matches,items:d.items,note:'当前 RSS 源题名本地筛选，非完整期刊库或历史检索；不证明全部内容或 AI 使用权限。'};
}
