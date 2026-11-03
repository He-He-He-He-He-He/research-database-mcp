/** 知领政策库：复用已登录浏览器标签，仅读取标题检索第一页。 */
export async function zhilinPolicySearch(tab,query){
 if(typeof query!=='string'||!query.trim()||query.length>100||/[\x00-\x1f]/.test(query))throw Error('关键词须为1–100字且无控制字符');
 const term=query.trim();const p=new URLSearchParams({policyType:'',shortname:'TI',word:term});
 await tab.goto('https://policy.ckcest.cn/search?'+p);
 let d;
 try{await tab.playwright.locator('#base-result-count').waitFor({state:'visible',timeoutMs:10000});}catch(_){}
 for(let i=0;i<8;i++){
  await tab.getAXState({emit:false});
  d=await tab.playwright.evaluate(()=>({url:location.href,logged:!!document.querySelector('#link_logout'),summary:document.querySelector('#base-result')?.innerText||'',items:[...document.querySelectorAll('.search-result-list')].filter(e=>e.getClientRects().length).map(e=>({id:e.getAttribute('code'),title:e.querySelector('h2 a')?.innerText.trim(),type:e.querySelector('h2 .g-text')?.innerText.trim(),issuer:e.querySelector('.publisher span')?.innerText.trim()||null,date:e.querySelector('.policy_time span')?.innerText.trim()||null}))}));
  const u=new URL(d.url);if(u.hostname!=='policy.ckcest.cn'||u.pathname!=='/search'||u.searchParams.get('word')!==term||u.searchParams.get('shortname')!=='TI')throw Error('未到达对应标题检索页，可能登录过期');
  if(!d.logged)throw Error('知领会话未登录');
  if(/找到\s*[\d,]+\s*条记录/.test(d.summary)&&(d.items.length||/找到\s*0\s*条记录/.test(d.summary)))break;
 }
 const m=d?.summary.match(/找到\s*([\d,]+)\s*条记录/);if(!m||(+m[1].replaceAll(',','')>0&&!d.items.length))throw Error('结果未加载，不能判断为空');
 const items=d.items.map(x=>{if(!/^[0-9a-f]{32}$/i.test(x.id)||!x.title)throw Error('结果结构异常');return {...x,url:'https://policy.ckcest.cn/detail/'+x.id+'.html'};});
 return {source:'知领政策库',query:term,query_field:'标题',total:Number(m[1].replaceAll(',','')),items,note:'个人登录会话的标题检索首屏；并非学校身份或逐条政策效力、正文权限的证明。'};
}
