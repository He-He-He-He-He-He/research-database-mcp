/** De Gruyter Brill public math journal results, using a caller-provided browser tab. */
export async function degruyterMathJournals(tab, query) {
  if (typeof query !== 'string' || !query.trim() || query.length > 200) throw Error('关键词须为 1–200 个字符');
  const params = new URLSearchParams({query:query.trim(),startItem:'0',pageSize:'10',sortBy:'relevance',documentVisibility:'all',subjectFacet:'MT',documentTypeFacet:'journal'});
  await tab.goto('https://www.degruyterbrill.com/search?'+params);
  await tab.playwright.locator('#searchResultsContent').waitFor({state:'visible',timeoutMs:30000});
  let complete=false;
  for(let attempt=0;attempt<60;attempt++) {
    complete=await tab.playwright.evaluate(()=>{
      const text=document.querySelector('#pageSizeAndSortForm')?.innerText||'';
      const m=text.match(/\b(\d[\d,]*)\s+of\s+(\d[\d,]*)\s+results/i);
      return !!m && document.querySelectorAll('#searchResultsItems .searchResult .resultTitle h3').length >= Number(m[1].replaceAll(',',''));
    });
    if(complete) break;
    await new Promise(r=>setTimeout(r,250));
  }
  if(!complete) throw Error('未确认结果条数，可能无结果、页面变更或加载失败');
  const result = await tab.playwright.evaluate((q)=>{
    const p=new URL(location.href).searchParams;
    if(p.get('query')!==q || p.get('subjectFacet')!=='MT' || p.get('documentTypeFacet')!=='journal') throw Error('未确认关键词及数学期刊筛选');
    const text=document.querySelector('#pageSizeAndSortForm')?.innerText || '';
    const m=text.match(/\b(\d[\d,]*)\s+of\s+(\d[\d,]*)\s+results/i);
    return {source:'De Gruyter Brill 数学期刊公开结果', query:q, total:m?Number(m[2].replaceAll(',','')):null,
      institution:document.body.innerText.includes('Zhejiang University')?'Zhejiang University':null,
      items:[...document.querySelectorAll('#searchResultsItems .searchResult')].map(c=>({
        title:c.querySelector('.resultTitle h3')?.textContent.trim()||null,
        url:c.querySelector('.resultTitle a')?.href||null,
        type:c.querySelector('.newResultType')?.innerText.trim()||null,
        access:c.querySelector('.contentAvailability')?.getAttribute('title')||null
      })).filter(x=>x.title&&x.url),
      note:'出版社数学期刊全库结果，并非确认学校订购清单；仅当前页，机构身份和全文权限未验证，匹配可能来自期刊介绍。'};
  },query.trim());
  if(!result.items.length && result.total !== 0) throw Error('未识别结果；可能无结果、上游页面变更或拦截');
  return result;
}
