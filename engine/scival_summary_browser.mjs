/** 读取当前已登录 SciVal 机构 Summary 页的可见指标。 */
export async function scivalInstitutionSummary(tab){
 const d=await tab.playwright.evaluate(()=>{
  const u=new URL(location.href),body=document.querySelector('#overallResearchPerformanceDashboard')?.innerText||'',range=document.querySelector('#yearRangeSelector')?.innerText.trim(),institution=document.querySelector('h1')?.innerText.trim();
  const value=(label)=>{const lines=body.split('\n').map(x=>x.trim()).filter(Boolean);const i=lines.findIndex(x=>x===label);if(i<0)return null;for(let j=i-1;j>=Math.max(0,i-3);j--)if(/^[\d,.]+%?$/.test(lines[j]))return lines[j];return null};
  const pub=document.querySelector('#overallResearchPerformance_publicationCount')?.innerText.match(/^[\d,]+/)?.[0]||null;
  const authors=document.querySelector('#overallResearchPerformance_publishedResearchers')?.innerText.match(/^[\d,]+/)?.[0]||null;
  const oa=document.querySelector('#overallResearchPerformance_openAccess button')?.innerText.trim()||null;
  return {host:u.hostname,path:u.pathname,uri:u.searchParams.get('uri'),institution,range,pub,authors,oa,mean:value('Field-Weighted Citation Impact (Mean)'),median:value('Field-Weighted Citation Impact (Median)'),citations:value('Citation Count'),perPublication:value('Citations per Publication'),h5:value('h5-index')};
 });
 if(d.host!=='www.scival.com'||d.path!=='/overview/summary'||!/^Institution\/\d+$/.test(d.uri||'')||!d.institution||!/^\d{4}\s*-\s*\d{4}$/.test(d.range||'')||!d.pub||!d.authors||!d.citations)throw Error('当前标签不是已加载的 SciVal 机构 Summary 指标页');
 return {source:'SciVal',institution:d.institution,entity:d.uri,yearRange:d.range,scholarlyOutput:d.pub,authors:d.authors,openAccess:d.oa,fwciMean:d.mean,fwciMedian:d.median,citationCount:d.citations,citationsPerPublication:d.perPublication,h5Index:d.h5,note:'当前页面可见指标；保留页面时间范围及指标定义，其他设置和权限未验证。'};
}
