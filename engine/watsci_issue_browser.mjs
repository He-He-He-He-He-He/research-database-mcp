/** Capture one visible DCDIS A/B issue response; original-language title and author markup. */
export function parseWatsciIssue(raw,path,limit=10){
 if(typeof raw!=='string'||raw.length>2_000_000||typeof path!=='string'||!/^\/contents20\d\d\/v\d+n\d+[ab]\.html$/.test(path)||!Number.isInteger(limit)||limit<1||limit>50)throw Error('卷期参数或响应异常');
 const series=path.match(/([ab])\.html$/)[1].toUpperCase();
 if(!raw.includes('TABLE OF CONTENTS')||!new RegExp(`Series\\s*${series}\\s*:`, 'i').test(raw))throw Error('响应未确认系列及目录');
 const rows=[];const re=/<strong>\s*<a\s+href=["']([^"']*abstract_pdf[^"']+)["'][^>]*>([\s\S]*?)<\/a>\s*<\/strong>\s*<br\s*\/?\s*>\s*<em>([\s\S]*?)<\/em>[\s\S]*?Pages\s+([\d]+\s*[-–]\s*[\d]+)/gi;
 for(const m of raw.matchAll(re)){let u=new URL(m[1],'https://online.watsci.org'+path);if(u.hostname!=='online.watsci.org'||!u.pathname.startsWith('/abstract_pdf/'))throw Error('题录链接异常');const clean=x=>x.replace(/<[^>]*>/g,' ').replace(/\s+/g,' ').trim();rows.push({title_raw_html:clean(m[2]),authors_raw_html:clean(m[3]),pages_raw:m[4],abstract_pdf:u.href})}
 if(!rows.length)throw Error('未识别期刊题录');return {source:'DCDIS 官方在线卷期目录',series,issue_path:path,items:rows.slice(0,limit),note:'原始标题与作者保留 HTML 实体；仅卷期题录，未验证学校机构或全文权限。'};
}
export async function watsciIssue(tab,reloadIssue,limit=10){
 if(typeof reloadIssue!=='function')throw Error('需要当前卷期正常刷新回调');let u=new URL(await tab.url());if(u.hostname!=='online.watsci.org'||!/^\/contents20\d\d\/v\d+n\d+[ab]\.html$/.test(u.pathname))throw Error('当前页面不是指定卷期');
 const c=await tab.capabilities.get('cdp'),methods=['Network.responseReceived','Network.loadingFinished','Network.loadingFailed'];await c.send('Network.enable');let cursor=(await c.readEvents({methods})).cursor;await reloadIssue();let id,done=false,deadline=Date.now()+20000;
 while(Date.now()<deadline){let e=await c.readEvents({methods,afterSequence:cursor,timeoutMs:1500,limit:500});cursor=e.cursor;if(e.truncated)throw Error('网络事件不完整');for(let x of e.events){let p=x.params||{};if(x.method==='Network.responseReceived'&&p.type==='Document'&&p.response?.status===200){let v;try{v=new URL(p.response.url)}catch{}if(v?.hostname===u.hostname&&v.pathname===u.pathname)id=p.requestId}if(id&&p.requestId===id&&x.method==='Network.loadingFinished')done=true;if(id&&p.requestId===id&&x.method==='Network.loadingFailed')throw Error('卷期响应失败')}
 if(done){let b=await c.send('Network.getResponseBody',{requestId:id});let raw=b.base64Encoded?Buffer.from(b.body,'base64').toString('utf8'):b.body;let now=new URL(await tab.url());if(now.hostname!==u.hostname||now.pathname!==u.pathname)throw Error('卷期页面已改变');return parseWatsciIssue(raw,u.pathname,limit)}await new Promise(r=>setTimeout(r,200))}throw Error('未收到卷期响应');
}
