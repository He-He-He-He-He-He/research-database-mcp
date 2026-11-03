/** Capture one ordinary Beck search response in the current Zhejiang University browser session. */
export function checkBeckSearch(body, state, query, limit=5) {
 if(typeof body!=='string'||body.length>15_000_000||!state||typeof query!=='string'||!query.trim()||query.length>100||!Number.isInteger(limit)||limit<1||limit>10) throw Error('检索参数或响应异常');
 if(state.query!==query.trim()||!state.scope?.includes('nur in meinen Modulen')||!Array.isArray(state.records)) throw Error('页面未确认查询词与学校订购范围');
 const rows=state.records.slice(0,limit);
 if(!rows.length) throw Error('未取得页面记录；空结果或页面结构变化需要人工核验');
 for(const r of rows){if(!/^\d+$/.test(r.id)||!r.title||!r.source||!/^\/Dokument\?/.test(r.path)||!body.includes(`id="${r.id}"`))throw Error('页面题录与本次响应不一致')}
 return {source:'Beck Online（当前机构订购集合）',query:query.trim(),scope:'当前会话的订购集合；未限定单个子库',records:rows,note:'本次结果页未重新校验机构名称；仅题录。页面声明相关内容用于 AI 需另行授权。机构授权及订购范围可能变化。'};
}
export async function beckInstitutionSearch(tab,query,submitSearch,limit=5){
 if(typeof submitSearch!=='function'||typeof query!=='string'||!query.trim()||query.length>100)throw Error('检索参数无效');
 let c=await tab.capabilities.get('cdp'),methods=['Network.responseReceived','Network.loadingFinished','Network.loadingFailed'];await c.send('Network.enable');let cursor=(await c.readEvents({methods})).cursor;await submitSearch();let id,done=false,deadline=Date.now()+20000;
 while(Date.now()<deadline){let ev=await c.readEvents({methods,afterSequence:cursor,timeoutMs:1500,limit:500});cursor=ev.cursor;if(ev.truncated)throw Error('网络事件不完整');for(const e of ev.events){const p=e.params||{};if(e.method==='Network.responseReceived'&&p.type==='Document'&&p.response?.status===200){let u;try{u=new URL(p.response.url)}catch{}if(u?.hostname==='beck-online.beck.de'&&u.pathname==='/Search'&&u.searchParams.get('words')===query.trim())id=p.requestId}if(id&&p.requestId===id&&e.method==='Network.loadingFinished')done=true;if(id&&p.requestId===id&&e.method==='Network.loadingFailed')throw Error('检索响应失败')}
 if(done){const body=await c.send('Network.getResponseBody',{requestId:id});if(body.base64Encoded)throw Error('响应编码不支持');let state=await tab.playwright.evaluate(()=>({query:document.querySelector('#words')?.value,scope:document.querySelector('#treffbalken')?.innerText,records:[...document.querySelectorAll('li.main-background, li.alternative-background')].filter(e=>e.querySelector('h2.sndline a')).map(e=>({id:e.id,title:e.querySelector('h2.sndline a')?.innerText?.trim(),source:e.querySelector('.treffer-firstline-text a')?.innerText?.trim(),path:e.querySelector('h2.sndline a')?.getAttribute('href')}))}));return checkBeckSearch(body.body,state,query,limit)}
 await new Promise(r=>setTimeout(r,200));}throw Error('未收到当前查询的完整响应');
}
