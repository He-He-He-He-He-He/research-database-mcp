/** Capture one normal InCites organizations analysis table response. */
function matches(url, post, start, end) {
  try {
    const u = new URL(url), p = JSON.parse(post), f = p.filters;
    return u.origin === 'https://incites.clarivate.com' && u.pathname === '/route/incites-app/explore/0/organization/data/table/page' && u.searchParams.get('queryDataCollection') === 'ESCI' &&
      JSON.stringify(f.period?.is) === JSON.stringify([start,end]) && f.schema?.is === 'Web of Science' && f.geographicCollabType?.is === 'All' && f.publisherType?.is === 'All' && f.fundingAgencyType?.is === 'All' && f.fundingDataSource?.is === 'All Sources' &&
      Object.keys(f).sort().join(',') === ['earlyAccess','fundingAgencyType','fundingDataSource','geographicCollabType','period','personIdType','personIdTypeGroup','publisherType','schema'].sort().join(',') &&
      f.personIdType?.is === 'authorRecord' && f.personIdTypeGroup?.is === 'authorRecord' && JSON.stringify(f.earlyAccess?.is) === '[1]' &&
      p.skip === 0 && p.take === 25 && p.sortBy === 'timesCited' && p.sortOrder === 'desc' && Array.isArray(p.pinned) && !p.pinned.length && Array.isArray(p.groupPinned) && !p.groupPinned.length && Array.isArray(p.indicators) && ['orgName','wosDocuments','timesCited','cnorm','percentCited','rank','norm','key'].every(x=>p.indicators.includes(x));
  } catch { return false; }
}
export function parseIncitesOrganizations(body) {
  const data=JSON.parse(body);
  if (!Array.isArray(data.items) || data.items.length > 25) throw Error('InCites 机构表响应异常');
  return data.items.map(x=>{
    if (typeof x.orgName!=='string' || typeof x.key!=='string' || typeof x.wosDocuments?.value!=='number' || typeof x.timesCited!=='number') throw Error('机构行字段异常');
    return {id:x.key,organization:x.orgName,documents:x.wosDocuments.value,timesCited:x.timesCited,collabCNCI:x.cnorm??null,percentCited:x.percentCited??null,rank:x.rank??null,categoryNormalizedCitationImpact:x.norm??null};
  });
}
export async function incitesOrganizationsResponse(tab, start, end, submitSearch) {
  if (!Number.isInteger(start) || !Number.isInteger(end) || start>end || start<1900 || end>2100 || typeof submitSearch!=='function') throw Error('需要有效的出版年份范围及普通页面重载回调');
  const c=await tab.capabilities.get('cdp'); await c.send('Network.enable');
  const methods=['Network.requestWillBeSent','Network.responseReceived','Network.loadingFinished']; let cur=(await c.readEvents({methods})).cursor;
  await submitSearch(); const ids=new Set(), ok=new Set(), done=new Set();
  for (let deadline=Date.now()+30000; Date.now()<deadline;) {
    const e=await c.readEvents({afterSequence:cur,methods,limit:1000,timeoutMs:1000});cur=e.cursor;if(e.truncated)throw Error('网络事件不完整');
    for(const x of e.events){const p=x.params||{};if(x.method==='Network.requestWillBeSent'&&p.request?.method==='POST'&&matches(p.request.url,p.request.postData||'',start,end))ids.add(p.requestId);if(x.method==='Network.responseReceived'&&p.response?.status===200)ok.add(p.requestId);if(x.method==='Network.loadingFinished')done.add(p.requestId);}
    const id=[...ids].find(i=>ok.has(i)&&done.has(i));if(!id)continue;
    let state; for(let until=Date.now()+10000;Date.now()<until;) { state=await tab.playwright.evaluate(()=>({host:location.hostname,path:location.hash,text:document.body.innerText})); if(state.host==='incites.clarivate.com'&&state.path==='#/analysis/0/organization'&&state.text.includes(`${start} to ${end}`))break; await new Promise(r=>setTimeout(r,200)); }
    if(!state||state.host!=='incites.clarivate.com'||state.path!=='#/analysis/0/organization'||!state.text.includes(`${start} to ${end}`))throw Error('当前页面或出版时间范围不符');
    const b=await c.send('Network.getResponseBody',{requestId:id});const body=b.base64Encoded?Buffer.from(b.body,'base64').toString('utf8'):b.body;
    return {source:'Clarivate InCites',period:[start,end],dataset:'InCites Dataset, Web of Science, includes ESCI',sort:'timesCited descending',items:parseIncitesOrganizations(body),scope:'默认机构分析表首屏最多25行，按被引次数排序；非全库或全文。时间、指标定义、来源更新和权限以当前页面为准；机构间比较需考虑学科差异。'};
  }
  throw Error('未捕获匹配的 InCites 机构分析响应');
}
