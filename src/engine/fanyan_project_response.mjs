/** 泛研已登录检索页：通过用户可见分页动作观察本页实际响应，只读一页。 */
export async function fanyanProjectPage(tab,page){
 if(!Number.isInteger(page)||page<1||page>100000)throw Error('页码无效');
 let state=await tab.playwright.evaluate(()=>({host:location.hostname,path:location.pathname,logged:!!document.querySelector('a[href="/logout"]'),query:document.querySelector('#guanJianCi1')?.value?.trim(),active:Number(document.querySelector('.pagination li.active')?.innerText),total:document.querySelector('#TotalText')?.innerText}));
 if(state.host!=='www.funresearch.cn'||state.path!=='/project/list'||!state.logged||!state.query)throw Error('请先以已登录会话打开项目检索结果');
 if(state.active===page)throw Error('目标页已打开；请选择当前页面显示的其他页');
 const locator=tab.playwright.locator('.page-link').filter({hasText:new RegExp('^'+page+'$')}).first();
 if(!await locator.count())throw Error('目标页不在当前可见分页范围');
 const c=await tab.capabilities.get('cdp');await c.send('Network.enable');let cur=(await c.readEvents({methods:['Network.requestWillBeSent','Network.responseReceived']})).cursor;
 await locator.click();let requestId=null, ids=new Set();
 for(let i=0;i<12&&!requestId;i++){
  const es=await c.readEvents({afterSequence:cur,methods:['Network.requestWillBeSent','Network.responseReceived'],timeoutMs:3000,limit:500});cur=es.cursor;if(es.truncated)throw Error('网络事件不完整');
  for(const e of es.events){let p=e.params||{};if(e.method==='Network.requestWillBeSent'&&p.request?.url?.split('?')[0]==='https://www.funresearch.cn/project/items'&&p.request.method==='POST')ids.add(p.requestId);
   if(e.method==='Network.responseReceived'&&ids.has(p.requestId)&&p.response?.status===200&&p.response?.mimeType==='application/json')requestId=p.requestId;}
 }
 if(!requestId)throw Error('未观察到分页的成功响应');
 const raw=await c.send('Network.getResponseBody',{requestId});if(raw.base64Encoded)throw Error('不支持编码响应');const json=JSON.parse(raw.body);
 if(json.OF!==(page-1)*20||json.SZ!==20||typeof json.Items!=='string')throw Error('响应分页不一致');
 const data=await tab.playwright.evaluate(()=>({logged:!!document.querySelector('a[href="/logout"]'),query:document.querySelector('#guanJianCi1')?.value?.trim(),active:Number(document.querySelector('.pagination li.active')?.innerText),total:document.querySelector('#TotalText')?.innerText,items:[...document.querySelectorAll('.result_group_content')].filter(e=>e.getClientRects().length).map(e=>{let a=[...e.querySelectorAll('.p_title a')],p=[...e.querySelectorAll('.p_other>div')].filter(x=>x.getClientRects().length).map(x=>x.innerText.trim());return {id:e.querySelector('input[name="cb_results"]')?.value,title:a[0]?.innerText.trim(),fund:a[1]?.innerText.trim()||null,category:a[2]?.innerText.trim()||null,year:e.querySelector('.p_title>span:last-child')?.innerText.trim()||null,details:p};})}));
 if(!data.logged||data.query!==state.query||data.active!==page||!data.items.length)throw Error('页面状态与请求不符或结果尚未加载');
 for(const item of data.items){if(!item.id||!item.title||!json.Items.includes(item.id))throw Error('页面条目与响应不一致');}
 return {source:'泛研全球科研项目数据库实际分页响应',query:state.query,page,total:Number(data.total.replaceAll(',','')),items:data.items,note:'单次读取用户可见一页；智能检索默认关联项目与成果，题录非官方立项原始公告，机构授权及准确性须逐项核查。'};
}
