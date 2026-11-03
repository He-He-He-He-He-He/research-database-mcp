/** CSMAR 已登录 CUA 标签页的只读目录检索。
 * 使用前通过 CUA 绑定用户已登录的 https://data.csmar.com/ 页面。
 * 不读取、保存或输出 Cookie、令牌、密码；一次调用触发一次网站正常搜索。
 * 注意网站在搜索时可能自动记录访问日志；本模块不下载或导出数据。
 */
export async function searchCSMAR(tab, keyword) {
  if (typeof keyword !== 'string' || !keyword.trim() || keyword.length > 100 || /[\r\n]/.test(keyword))
    throw new Error('关键词必须为 1–100 字的单行文本');
  const query = keyword.trim();
  const state = await tab.getAXState({ emit: false, disableDiffing: true });
  if (!state.includes('data.csmar.com/')) throw new Error('请绑定 CSMAR 标签页');
  if (state.includes('账号登录') || state.includes('扫码登录')) throw new Error('请先完成 CSMAR 登录');
  const field = state.match(/\n\s*(\d+) text field \(settable\)/);
  if (!field) throw new Error('页面没有可用搜索框；请打开 CSMAR 首页或普通检索页');
  const cdp = await tab.capabilities.get('cdp');
  await cdp.send('Network.enable');
  let cursor = (await cdp.readEvents()).cursor;
  await tab.setValue(Number(field[1]), query);
  await tab.pressKey(Number(field[1]), 'Return');
  let requestId = null;
  for (let i = 0; i < 10; i++) {
    const result = await cdp.readEvents({ afterSequence: cursor,
      methods: ['Network.requestWillBeSent', 'Network.responseReceived'], timeoutMs: 3000, limit: 100 });
    cursor = result.cursor;
    if (result.truncated) throw new Error('浏览器请求记录已截断，无法验证本次检索');
    for (const event of result.events) {
      if (event.method === 'Network.requestWillBeSent') {
        const request = event.params?.request;
        if (request?.url?.split('?')[0] !== 'https://data.csmar.com/api/csmar-main/highlight/searchData' || request.method !== 'POST') continue;
        let payload;
        try { payload = JSON.parse(request.postData || '{}'); } catch { continue; }
        if (payload.searchKey === query && payload.pageNo === 1) requestId = event.params.requestId;
      }
      if (event.method === 'Network.responseReceived' && requestId && event.params?.requestId === requestId) {
        if (event.params.response.status !== 200) throw new Error('CSMAR 检索请求失败：HTTP ' + event.params.response.status);
        const response = await cdp.send('Network.getResponseBody', { requestId });
        if (response.base64Encoded) throw new Error('响应编码暂不支持');
        let data; try { data = JSON.parse(response.body); } catch { throw new Error('CSMAR 返回非 JSON 响应'); }
        if (data.code !== 0) throw new Error('CSMAR 返回错误：' + String(data.msg || data.code));
        return { query, source: 'CSMAR 普通检索 searchData', data: data.data };
      }
    }
  }
  throw new Error('未观察到本次检索的成功响应；请检查登录状态或页面是否改版');
}
