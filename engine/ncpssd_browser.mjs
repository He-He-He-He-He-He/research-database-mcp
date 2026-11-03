/* 国家哲学社会科学文献中心，CUA 后台工作页单页检索。 */
import { Buffer } from 'node:buffer';
export async function ncpssdSearch(tab, keyword) {
  if(typeof keyword!=='string'||!keyword.trim()||keyword.length>80||/["\x00-\x1f]/.test(keyword)) throw Error('关键词需 1–80 字且不能含双引号或控制字符');
  const k=keyword.trim(), b=s=>Buffer.from(s,'utf8').toString('base64');
  const expr=`(IKTE="${k}" OR IKPYTE="${k}"  OR IKST="${k}" OR IKET="${k}" OR IKSE="${k}")`;
  const u=new URL('https://www.ncpssd.org/Literature/articlelist');
  u.search=new URLSearchParams({sType:'0',search:b(expr),searchname:b(`题名/关键词="${k}"`),nav:'0',ajaxKeys:b(k)}).toString();
  await tab.goto(u.toString());
  try{await tab.playwright.locator('#ul_articlelist > li .julei-list > a[data-id]').first().waitFor({state:'visible',timeoutMs:15000});}
  catch(_){throw Error('没有读到结果，请检查登录、无结果、网站页面或验证状态；不自动重试。');}
  const data=await tab.playwright.evaluate(()=>({
    institution:document.body.innerText.includes('浙江大学')?'浙江大学':null,
    items:[...document.querySelectorAll('#ul_articlelist > li')].map(li=>{let a=li.querySelector('.julei-list > a[data-id]');let fields=[...li.querySelectorAll(':scope > p')].map(p=>p.innerText.trim());return {title:a?.innerText.trim(),id:a?.getAttribute('data-id'),type:a?.getAttribute('data-type'),fields};}).filter(x=>x.title)
  }));
  return {source:'国家哲学社会科学文献中心',query:k,page:1,...data,note:'当前页题录和摘要；具体身份与全文访问权限需以网站实时状态为准。'};
}
