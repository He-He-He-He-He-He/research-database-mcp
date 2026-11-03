/** 文心閣正文关键词查询的首屏书目信息；不读取正文。 */
export async function wenxingeSearch(tab,query){
 if(typeof query!=='string'||!query.trim()||query.length>100||/["\x00-\x1f]/.test(query))throw Error('关键词须为1–100字且不含引号或控制字符');
 const term=query.trim();
 try{await tab.goto('https://www.wenxin-ge.com/wenxinge/home/doc/index.do');}catch(e){
  if(!String(e).includes('Timed out waiting for tab'))throw e;
  const p=await tab.playwright.evaluate(()=>({url:location.href,field:!!document.querySelector('#searchWord')}));
  if(p.url!=='https://www.wenxin-ge.com/wenxinge/home/doc/index.do'||!p.field)throw e;
 }
 const state=await tab.getAXState({emit:false,disableDiffing:true});
 const field=state.match(/\b(\d+) text field \(settable\)[^\n]*(?:ID: )?searchWord/);
 if(!field)throw Error('未识别关键词输入框');
 await tab.setValue(Number(field[1]),term);await tab.pressKey(Number(field[1]),'Return');
 let ready=false;
 for(let i=0;i<15;i++){
  try{await tab.playwright.locator('#tablelist td.labellistbk').first().waitFor({state:'visible',timeoutMs:5000});}catch(_){}
  const test=await tab.playwright.evaluate(()=>({summary:document.querySelector('#showCountContent')?.innerText||'',rows:document.querySelectorAll('#tablelist tr td.labellistbk').length}));
  if(test.summary.includes('"'+term+'"')&&/共在\s*\d+\s*本中找到\s*\d+\s*筆/.test(test.summary)&&test.rows>0){ready=true;break;}
  await tab.getAXState({emit:false});
 }
 if(!ready)throw Error('未确认检索结果加载完成，可能无结果或页面错误');
 const d=await tab.playwright.evaluate(()=>({summary:document.querySelector('#showCountContent')?.innerText||'',institution:document.body.innerText.includes('用户：浙江大学')?'浙江大学':null,items:[...document.querySelectorAll('#tablelist tr')].filter(tr=>tr.getClientRects().length).map(tr=>{let t=[...tr.querySelectorAll(':scope > td')];return t.length>=4&&/^\d+$/.test(t[0].innerText.trim())?{index:Number(t[0].innerText.trim()),bibliography:t[1].innerText.trim(),dynasty:t[2].innerText.trim()||null,edition:t[3].innerText.trim()||null}:null}).filter(Boolean)}));
 const m=d.summary.match(/共在\s*(\d+)\s*本中找到\s*(\d+)\s*筆/);
 if(!d.summary.includes('"'+term+'"')||!m||!d.items.length)throw Error('检索词与结果不一致或结果不可读');
 return {source:'文心阁古籍数据库',query:term,institution:d.institution,matched_books:Number(m[1]),matched_hits:Number(m[2]),items:d.items,note:'正文关键词匹配所得当前页书目，并非书名检索；未读取正文或确认全文权限。'};
}
