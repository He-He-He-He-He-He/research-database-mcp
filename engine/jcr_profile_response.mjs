/** Capture four responses from a normal JCR journal profile refresh in an authorized session. */
const PATHS=['journal-information','journal-citationIndicator','jif-values','rank-byjif'];
export function parseJcrProfile(bodies,journal,year){
  const parsed=Object.fromEntries(PATHS.map(p=>[p,JSON.parse(bodies[p])]));
  if(PATHS.some(p=>parsed[p].status!=='Success')) throw Error('JCR 响应状态异常');
  const info=parsed['journal-information'].data,jci=parsed['journal-citationIndicator'],jif=parsed['jif-values'].data,rank=parsed['rank-byjif'].data;
  if(!info?.title||info.jcrAbbreviation!==journal||!Array.isArray(jif)||!Array.isArray(rank)||!Array.isArray(jci.data)) throw Error('JCR 响应结构或期刊不匹配');
  const current=jif.find(x=>x.withSelfCites)?.withSelfCites?.impactCurrent;
  return {source:'Clarivate Journal Citation Reports',journal:info.title,jcr_abbreviation:journal,year,issn:info.issn||null,eissn:info.eissn||null,editions:info.editions||[],jif:current??null,jci:jci.currentYearJci??null,categories:rank.map(x=>({category:x.category,edition:x.edition,rank:(x.combinedRankByJif||[]).find(r=>r.year===year)||(x.rankByJif||[]).find(r=>r.year===year)||null})),note:'单个期刊指定 JCR 年度的正常页面响应；JIF 和类别分区为期刊指标，不可直接评价个人或文章。跨年比较须注意学科分类与版次变化。其他指标及权限按平台原页核对。'};
}
export async function jcrProfileResponse(tab,journal,year,submitRefresh){
  if(typeof journal!=='string'||!journal.trim()||journal.length>100||!/^\d{4}$/.test(String(year))||typeof submitRefresh!=='function') throw Error('需要期刊 JCR 缩写、四位年份和正常页面刷新回调');
  journal=journal.trim();year=String(year);
  const state=await tab.playwright.evaluate(()=>({host:location.hostname,path:location.pathname,journal:new URL(location.href).searchParams.get('journal'),year:new URL(location.href).searchParams.get('year')}));
  if(state.host!=='jcr.clarivate.com'||state.path!=='/jcr-jp/journal-profile'||state.journal!==journal||state.year!==year) throw Error('当前页期刊或 JCR 年份不匹配');
  const c=await tab.capabilities.get('cdp');await c.send('Network.enable');const methods=['Network.requestWillBeSent','Network.responseReceived','Network.loadingFinished'];let cursor=(await c.readEvents({methods})).cursor;
  await submitRefresh();const ids={},ok=new Set(),done=new Set();
  for(let end=Date.now()+30000;Date.now()<end;){
    const batch=await c.readEvents({afterSequence:cursor,methods,limit:1000,timeoutMs:1000});cursor=batch.cursor;if(batch.truncated)throw Error('网络事件不完整');
    for(const ev of batch.events){const p=ev.params||{};
      if(ev.method==='Network.requestWillBeSent'&&p.request?.method==='POST') try {const u=new URL(p.request.url), data=JSON.parse(p.request.postData||'{}'),name=u.pathname.split('/').pop();if(u.origin==='https://jcr.clarivate.com'&&u.pathname===`/api/jcr3/journalprofile/v1/${name}`&&PATHS.includes(name)&&data.journal===journal&&(name==='rank-byjif'?Object.keys(data).length===1:data.year===year&&Object.keys(data).length===2))ids[name]=p.requestId;} catch{}
      if(ev.method==='Network.responseReceived'&&p.response?.status===200)ok.add(p.requestId);
      if(ev.method==='Network.loadingFinished')done.add(p.requestId);
    }
    if(PATHS.every(x=>ids[x]&&ok.has(ids[x])&&done.has(ids[x]))){
      const final=await tab.playwright.evaluate(()=>({host:location.hostname,path:location.pathname,journal:new URL(location.href).searchParams.get('journal'),year:new URL(location.href).searchParams.get('year'),title:document.querySelector('#journal-info')?.innerText.trim()}));
      if(final.host!=='jcr.clarivate.com'||final.path!=='/jcr-jp/journal-profile'||final.journal!==journal||final.year!==year||!final.title)throw Error('结果页无法验证');
      const bodies={};for(const p of PATHS){const v=await c.send('Network.getResponseBody',{requestId:ids[p]});bodies[p]=v.base64Encoded?Buffer.from(v.body,'base64').toString('utf8'):v.body;}
      const result=parseJcrProfile(bodies,journal,year);if(result.journal!==final.title)throw Error('页面标题与响应不一致');return result;
    }
  }
  throw Error('未捕获完整的 JCR 期刊响应');
}
