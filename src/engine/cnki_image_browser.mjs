/** 读取学校现有会话中的知网学术图片库结果页标题；不抓取图片。 */
export async function cnkiImageSearch(tab, query) {
 if(typeof query!=='string'||query!==query.trim()||!query||query.length>100)throw Error('关键词需为 1–100 字');
 const u=new URL('https://image.cnki.net/search');u.searchParams.set('n',query);await tab.goto(u.href);
 for(let i=0;i<20;i++){
  const d=await tab.playwright.evaluate(()=>{const u=new URL(location.href),text=document.body.innerText,match=text.match(/找到相关信息共\s*([\d,]+)\s*条/);return {host:u.hostname,path:u.pathname,q:u.searchParams.get('n'),institution:text.includes('浙江大学图'),total:match?Number(match[1].replaceAll(',','')):null,titles:[...document.querySelectorAll('#waterfall .waterfall_text a')].map(x=>x.innerText.trim()).filter(Boolean)};});
  if(d.host==='image.cnki.net'&&d.path==='/search'&&d.q===query&&d.total!==null&&d.titles.length)return {source:'CNKI 学术图片库',query,total:d.total,institutionShown:d.institution,titles:d.titles,note:'当前结果页可见图片标题；不含图片、详情或来源文献，学校标识不证明下载权限。'};
  await new Promise(resolve=>setTimeout(resolve,500));
 }
 throw Error('未确认知网图片库结果；可能需要登录或安全验证，或结果为空');
}
