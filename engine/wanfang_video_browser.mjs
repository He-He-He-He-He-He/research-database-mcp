/* 万方视频检索首屏题录；不播放或下载视频。 */
export async function wanfangVideoSearch(tab, keyword, page=1) {
  if(typeof keyword!=='string'||!keyword.trim()||keyword.length>100||!Number.isInteger(page)||page<1||page>100) throw Error('关键词或页码不合法');
  const url='https://s.wanfangdata.com.cn/video?'+new URLSearchParams({q:keyword.trim(),p:String(page)});
  await tab.goto(url);
  try { await tab.playwright.locator('.video-item .vd-title').first().waitFor({state:'visible',timeoutMs:15000}); }
  catch (_) { throw Error('未读取视频结果；可能无结果、需要登录或页面变化。'); }
  const data=await tab.playwright.evaluate(()=>({institution:document.body.innerText.includes('浙江大学图书馆')?'浙江大学图书馆':null,items:[...document.querySelectorAll('.video-item')].map(e=>({title:e.querySelector('.vd-title')?.innerText.trim(),id:e.querySelector('.title-id-hidden')?.textContent.trim(),duration:e.querySelector('.vd-time')?.innerText.trim()})).filter(x=>x.title)}));
  return {source:'万方视频',page,url,...data,note:'当前页视频题录，不代表播放权限。'};
}
