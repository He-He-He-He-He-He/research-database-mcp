/** Capture one normal InCites organizations analysis table response. */
function matches(url, post, start, end, organization) {
  try {
    const u = new URL(url), p = JSON.parse(post), f = p.filters;
    return u.origin === 'https://incites.clarivate.com' && u.pathname === '/route/incites-app/explore/0/organization/data/table/page' && u.searchParams.get('queryDataCollection') === 'ESCI' &&
      JSON.stringify(f.period?.is) === JSON.stringify([start,end]) && JSON.stringify(f.orgname?.is) === JSON.stringify([organization]) && f.schema?.is === 'Web of Science' && f.geographicCollabType?.is === 'All' && f.publisherType?.is === 'All' && f.fundingAgencyType?.is === 'All' && f.fundingDataSource?.is === 'All Sources' &&
      Object.keys(f).sort().join(',') === ['earlyAccess','fundingAgencyType','fundingDataSource','geographicCollabType','orgname','period','personIdType','personIdTypeGroup','publisherType','schema'].sort().join(',') &&
      f.personIdType?.is === 'authorRecord' && f.personIdTypeGroup?.is === 'authorRecord' && JSON.stringify(f.earlyAccess?.is) === '[1]' &&
      p.skip === 0 && p.take === 25 && p.sortBy === 'timesCited' && p.sortOrder === 'desc' && Array.isArray(p.pinned) && !p.pinned.length && Array.isArray(p.groupPinned) && !p.groupPinned.length && Array.isArray(p.indicators) && ['orgName','wosDocuments','timesCited','cnorm','percentCited','rank','norm','key'].every(x=>p.indicators.includes(x));
  } catch { return false; }
}
function parseIncitesOrganizations(body) {
  const data=JSON.parse(body);
  if (!Array.isArray(data.items) || data.items.length > 25) throw Error('InCites 机构表响应异常');
  return data.items.map(x=>{
    if (typeof x.orgName!=='string' || typeof x.key!=='string' || typeof x.wosDocuments?.value!=='number' || typeof x.timesCited!=='number') throw Error('机构行字段异常');
    return {id:x.key,organization:x.orgName,documents:x.wosDocuments.value,timesCited:x.timesCited,collabCNCI:x.cnorm??null,percentCited:x.percentCited??null,rank:x.rank??null,categoryNormalizedCitationImpact:x.norm??null};
  });
}
export async function incitesOrganizationFilterResponse(tab, organization, start, end, submitSearch) {
  if (typeof organization!=='string' || !organization.trim() || organization.length>200 || organization!==organization.trim()) throw Error('需要机构完整名称');
  if (!Number.isInteger(start) || !Number.isInteger(end) || start>end || start<1900 || end>2100 || typeof submitSearch!=='function') throw Error('需要有效的出版年份范围及普通页面重载回调');
  const c=await tab.capabilities.get('cdp'); await c.send('Network.enable');
  const methods=['Network.requestWillBeSent','Network.responseReceived','Network.loadingFinished']; let cur=(await c.readEvents({methods})).cursor;
  await submitSearch(); const ids=new Set(), ok=new Set(), done=new Set();
  for (let deadline=Date.now()+30000; Date.now()<deadline;) {
    const e=await c.readEvents({afterSequence:cur,methods,limit:1000,timeoutMs:1000});cur=e.cursor;if(e.truncated)throw Error('网络事件不完整');
    for(const x of e.events){const p=x.params||{};if(x.method==='Network.requestWillBeSent'&&p.request?.method==='POST'&&matches(p.request.url,p.request.postData||'',start,end,organization))ids.add(p.requestId);if(x.method==='Network.responseReceived'&&p.response?.status===200)ok.add(p.requestId);if(x.method==='Network.loadingFinished')done.add(p.requestId);}
    const id=[...ids].find(i=>ok.has(i)&&done.has(i));if(!id)continue;
    let state; for(let until=Date.now()+10000;Date.now()<until;) { state=await tab.playwright.evaluate(()=>({host:location.hostname,path:location.hash,text:document.body.innerText})); if(state.host==='incites.clarivate.com'&&state.path==='#/analysis/0/organization'&&state.text.includes(`${start} to ${end}`) && state.text.includes(organization))break; await new Promise(r=>setTimeout(r,200)); }
    if(!state||state.host!=='incites.clarivate.com'||state.path!=='#/analysis/0/organization'||!state.text.includes(`${start} to ${end}`)||!state.text.includes(organization))throw Error('当前页面或出版时间范围不符');
    const b=await c.send('Network.getResponseBody',{requestId:id});const body=b.base64Encoded?Buffer.from(b.body,'base64').toString('utf8'):b.body;
    const items=parseIncitesOrganizations(body); if(items.some(x=>x.organization!==organization)) throw Error('返回机构与筛选不一致');
    return {source:'Clarivate InCites',organization,period:[start,end],dataset:'InCites Dataset, Web of Science, includes ESCI',sort:'timesCited descending',items,scope:'精确机构名称筛选首屏；返回 rank 是当前筛选结果内部位置，不是全库排名。非全文；机构名称须从站方候选选择，时间、指标和权限以当前页面为准。'};
  }
  throw Error('未捕获匹配的 InCites 机构分析响应');
}
