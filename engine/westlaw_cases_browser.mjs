/** Westlaw Classic: one bounded query in an already authenticated ZJU session.
 * Returns only visible case titles and count; no snippets, session URLs or full text.
 */
export async function westlawCasesSearch(tab, query, limit=3) {
  if (typeof query !== 'string' || !/^[\p{L}\p{N} .,'-]{1,100}$/u.test(query.trim())) throw Error('query must contain 1–100 ordinary characters');
  query=query.trim();
  if (!Number.isInteger(limit) || limit<1 || limit>5) throw Error('limit must be 1–5');
  const state=await tab.playwright.domSnapshot();
  if (!state.includes('Westlaw Classic') || !state.includes('Client ID:') || !state.includes('Westlaw Search.')) throw Error('Open the authenticated Westlaw Classic session first');
  const box=tab.playwright.getByRole('combobox',{name:/Westlaw Search/});
  await box.fill(query);
  await tab.playwright.getByRole('button',{name:'Search Westlaw'}).click();
  let result;
  for(let n=0;n<40;n++) {
    await tab.playwright.waitForTimeout(500);
    result=await tab.playwright.evaluate((max)=>{
      const u=new URL(location.href), h=document.querySelector('#cobalt_search_case_results_header');
      return {host:u.hostname,path:u.pathname,query:u.searchParams.get('query'),count:h?.querySelector('strong')?.textContent?.trim(),titles:[...document.querySelectorAll('#cobalt_search_case_results li h3')].slice(0,max).map(x=>x.textContent.trim())};
    },limit);
    if(result.host==='1.next.westlaw.com' && result.path==='/Search/Results.html' && result.query===query && result.count && result.titles.length) break;
  }
  if(!result || result.host!=='1.next.westlaw.com' || result.query!==query || !result.count || !result.titles.length) throw Error('Matching case overview not available; zero results or site state not verified');
  return {source:'Westlaw Classic via ZJU CARSI',query,case_count_display:result.count,items:result.titles.map(title=>({title})),scope:'current overview case titles only; current jurisdiction selection applies',note:'No full text or snippets. School agreement and permission for automated/AI use remain unverified; counts and access change.'};
}
