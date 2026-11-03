/** 观察浏览器实际搜索请求的响应；不读取、传递或保存认证信息。 */
export async function zhilinPolicyResponse(tab,query){
 if(typeof query!=='string'||!query.trim()||query.length>100||/[\x00-\x1f]/.test(query))throw Error('关键词须为1–100字且无控制字符');
 const term=query.trim(); const start=await tab.playwright.evaluate(()=>({host:location.hostname,logged:!!document.querySelector('#link_logout')}));
 if(start.host!=='policy.ckcest.cn'||!start.logged)throw Error('先在知领页面登录后再查询');
 const cdp=await tab.capabilities.get('cdp');await cdp.send('Network.enable');let cursor=(await cdp.readEvents({methods:['Network.requestWillBeSent','Network.responseReceived']})).cursor;
 await tab.goto('https://policy.ckcest.cn/search?'+new URLSearchParams({policyType:'',shortname:'TI',word:term}));
 try{await tab.playwright.locator('#base-result-count').waitFor({state:'visible',timeoutMs:10000});}catch(_){}
 const requests=new Map();let requestId=null;
 for(let i=0;i<10&&!requestId;i++){
  const ev=await cdp.readEvents({afterSequence:cursor,methods:['Network.requestWillBeSent','Network.responseReceived'],timeoutMs:3000,limit:500});cursor=ev.cursor;if(ev.truncated)throw Error('网络事件不完整');
  for(const e of ev.events){const p=e.params||{};
   if(e.method==='Network.requestWillBeSent'&&p.request?.url?.split('?')[0]==='https://policy.ckcest.cn/data/es/search'&&p.request.method==='POST'){
    let body;try{body=JSON.parse(p.request.postData||'');}catch(_){continue;}
    if(body.secondSearchExpress==='TI='+term&&body.page===1&&body.cnt===20&&Array.isArray(body.type)&&body.type.length===1&&body.type[0]==='1005')requests.set(p.requestId,true);
   }
   if(e.method==='Network.responseReceived'&&requests.has(p.requestId)&&p.response?.status===200&&p.response?.mimeType==='application/json')requestId=p.requestId;
  }
 }
 if(!requestId)throw Error('未确认本次检索的 JSON 响应');
 await tab.getAXState({emit:false});const pageState=await tab.playwright.evaluate(()=>({host:location.hostname,path:location.pathname,word:new URL(location.href).searchParams.get('word'),logged:!!document.querySelector('#link_logout')}));if(pageState.host!=='policy.ckcest.cn'||pageState.path!=='/search'||pageState.word!==term||!pageState.logged)throw Error('查询页面或登录状态不符');let raw;try{raw=await cdp.send('Network.getResponseBody',{requestId});}catch(_){throw Error('无法读取实际响应正文');}
 if(raw.base64Encoded)throw Error('不支持编码响应');let data;try{data=JSON.parse(raw.body);}catch(_){throw Error('结果不是有效 JSON');}
 const p=data.datas;if(!p||!Array.isArray(p.records)||typeof data.total!=='number'||p.current!==1||p.size!==20)throw Error('结果结构或分页不符');
 const strip=x=>typeof x==='string'?x.replace(/<\/?em>/g,''):null;
 const items=p.records.map(x=>{if(!/^[0-9a-f]{32}$/i.test(x._id)||typeof x.title!=='string')throw Error('结果缺少合法编号或标题');return {id:x._id,title:strip(x.title),type:x.policy_type||null,issuer:x.source_organization||null,publish_time_utc:x.publish_date||null,level:x.level_name||[],url:'https://policy.ckcest.cn/detail/'+x._id+'.html'};});
 return {source:'知领政策库浏览器会话实际 JSON 响应',query:term,query_field:'标题',total:data.total,page:p.current,page_size:p.size,items,note:'仅个人登录查询的实际响应；UTC 原始日期须按中国时区解释；未验证学校身份、正文或政策现行效力。'};
}
