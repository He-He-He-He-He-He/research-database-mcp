/** 读取用户正常打开的知网图片详情页可见题录，保留当前会话。 */
export async function cnkiImageDetail(tab){
 const d=await tab.playwright.evaluate(()=>{
  const u=new URL(location.href), title=document.title.replace(/--CNKI学术知识图片库\s*$/,'').trim();
  const li=[...document.querySelectorAll('li')].filter(x=>['图片来源：','图片关键词：','所属学科：'].includes(x.querySelector('span')?.innerText.trim()));
  const get=k=>li.find(x=>x.querySelector('span')?.innerText.trim()===k);
  const source=get('图片来源：')?.querySelector('p');
  const sourceText=[...source?.childNodes||[]].filter(x=>x.nodeType===3||x.nodeType===1&&x.tagName==='EM').map(x=>x.textContent.trim()).filter(Boolean).join(' ');
  const links=k=>[...get(k)?.querySelectorAll('p a')||[]].map(x=>x.innerText.trim()).filter(Boolean);
  return {host:u.hostname,path:u.pathname,title,source:sourceText,keywords:links('图片关键词：'),subject:links('所属学科：')};
 });
 if(d.host!=='image.cnki.net'||d.path!=='/detail'||!d.title||!d.source)throw Error('当前标签不是已加载的图片题录详情页');
 return {source:'CNKI 学术图片库',title:d.title,citation:d.source,keywords:d.keywords,subjects:d.subject,note:'当前详情页面可见题录；不包含图片、正文或下载链接。'};
}
