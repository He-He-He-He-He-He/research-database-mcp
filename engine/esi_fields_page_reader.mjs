/** Read the currently displayed ESI default research-fields table; no navigation or downloads. */
export async function esiResearchFieldsPage(tab, keyword='') {
  if(typeof keyword!=='string'||keyword.length>100) throw Error('关键词须为不超过 100 字符的字符串');
  return await tab.playwright.evaluate((q)=>{
    if(location.hostname!=='esi.clarivate.com'||!location.pathname.endsWith('/IndicatorsAction.action')) throw Error('请先在已登录的 ESI 指标页面打开默认 Research Fields 表');
    if(document.querySelector('#groupBy')?.value!=='Research Fields'||document.querySelector('#docType')?.value!=='Top') throw Error('请选择 Research Fields 和 Top Papers');
    if(document.querySelector('#filterPanel input[type=checkbox]:checked')) throw Error('请先清除筛选条件');
    const cols=[...document.querySelectorAll('#grid .x-column-header-text')].map(x=>x.innerText.trim());
    if(cols.slice(1).join('|')!=='Research Fields|Web of Science Documents|Cites|Cites/Paper|Top Papers') throw Error('指标列与已验证结构不符');
    const n=/^Total:\s*(\d+)$/.exec(cols[0]); if(!n) throw Error('无法确认总行数');
    const trs=[...document.querySelectorAll('#grid tr.x-grid-data-row')];
    if(trs.length!==Number(n[1])||trs.length!==22) throw Error('结果尚未完整显示或数据结构变更');
    const rows=trs.map(tr=>{
      const cells=[...tr.querySelectorAll(':scope > td')]; if(cells.length!==6) throw Error('指标行结构错误');
      const v=cells.map(c=>c.innerText.trim());
      const papers=cells[5].querySelector('.x-progress-text-back')?.innerText.trim();
      if(!/^\d+$/.test(v[0])||!v[1]||!/^\d[\d,]*$/.test(v[2])||!/^\d[\d,]*$/.test(v[3])||!/^\d+(\.\d+)?$/.test(v[4])||!papers||!/^\d[\d,]*$/.test(papers)) throw Error('指标值格式异常');
      const counts=[v[0],v[2],v[3],papers].map(x=>Number(x.replaceAll(',',''))); if(counts.some(x=>!Number.isSafeInteger(x))) throw Error('指标计数超出安全整数范围');
      return {rank:counts[0],field:v[1],documents:counts[1],cites:counts[2],cites_per_paper:Number(v[4]),cites_per_paper_display:v[4],top_papers:counts[3]};
    });
    const updated=(document.body.innerText.match(/InCites Essential Science Indicators dataset updated ([^.]+)\./)||[])[1]||null;
    if(!updated) throw Error('未确认数据更新时间');
    return {source:'Clarivate Essential Science Indicators', view:'Top Papers by Research Fields',updated,total:Number(n[1]),keyword:q,items:rows.filter(r=>r.field.toLowerCase().includes(q.toLowerCase())),note:'读取当前浏览器已显示的 22 个学科汇总行；非后台数据接口、机构排名或完整文献数据库。指标范围与窗口以平台说明为准；不保存会话标识。'};
  },keyword.trim());
}
