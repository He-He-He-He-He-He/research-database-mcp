/** CNRDS 目录关键词查询；需传入已通过学校或个人认证的 CUA 标签。 */
export async function searchCNRDS(tab, keyword) {
  if (typeof keyword !== 'string' || !keyword.trim() || keyword.length > 100 || /[\r\n]/.test(keyword))
    throw new Error('关键词必须为 1–100 字的单行文本');
  const query = keyword.trim();
  const state = await tab.getAXState({emit:false,disableDiffing:true});
  if (!state.includes('cnrds.com/Home/Index')) throw new Error('请先打开并登录 CNRDS');
  const match=state.match(/\n\s*(\d+) text field \(settable\)[^\n]*serach_input/);
  if (!match) throw new Error('未发现 CNRDS 目录检索框');
  const cdp=await tab.capabilities.get('cdp');
  await cdp.send('Network.enable');
  let cursor=(await cdp.readEvents()).cursor;
  await tab.setValue(Number(match[1]),query);
  let requestId=null;
  for (let i=0;i<10;i++) {
    const batch=await cdp.readEvents({afterSequence:cursor,methods:['Network.requestWillBeSent','Network.responseReceived'],timeoutMs:3000,limit:100});
    cursor=batch.cursor;
    if (batch.truncated) throw new Error('请求记录截断，不能确认查询');
    for (const e of batch.events) {
      if (e.method==='Network.requestWillBeSent') {
        const req=e.params?.request;
        if (!req?.url || req.method!=='GET') continue;
        let u; try { u=new URL(req.url); } catch { continue; }
        if (u.origin==='https://www.cnrds.com' && u.pathname==='/Home/SearchNew' && u.searchParams.get('text')===query && u.searchParams.get('opt')==='all') requestId=e.params.requestId;
      }
      if (e.method==='Network.responseReceived' && requestId && e.params?.requestId===requestId) {
        if(e.params.response.status!==200) throw new Error('CNRDS 检索失败 HTTP '+e.params.response.status);
        const body=await cdp.send('Network.getResponseBody',{requestId});
        if(body.base64Encoded) throw new Error('响应编码暂不支持');
        let items; try {items=JSON.parse(body.body)} catch {throw new Error('CNRDS 返回非 JSON，检查登录状态');}
        if(!Array.isArray(items)) throw new Error('CNRDS 返回异常，检查登录状态');
        return {query,source:'CNRDS 目录搜索',count:items.length,items};
      }
    }
  }
  throw new Error('未观察到本次查询的成功响应；请检查认证或页面更新');
}
