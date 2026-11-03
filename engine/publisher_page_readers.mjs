/**
 * 浙大机构会话内的单页元数据读取器。调用方必须注入 CUA 已绑定的、自己创建的工作 tab。
 * 只使用站点公开显示的结果和认证标识，不保存 Cookie、不下载 PDF、不自动翻页。
 * tab 对象需支持 goto、playwright.locator(...).waitFor 和 playwright.evaluate。
 */
export async function springerPage(tab, query) {
  if (!query?.trim()) throw Error('关键词不能为空');
  await tab.goto('https://link.springer.com/search?query=' + encodeURIComponent(query));
  await tab.playwright.locator('.app-card-open__main').first().waitFor({state:'visible',timeoutMs:15000});
  return await tab.playwright.evaluate(() => ({
    source:'Springer Nature Link',
    total:(document.body.innerText.match(/Showing\s+\d[\d,]*-\d[\d,]*\s+of\s+([\d,]+)\s+results/i)||[])[1]||null,
    institution:document.body.innerText.includes('Zhejiang University Library')?'Zhejiang University Library':null,
    items:Array.from(document.querySelectorAll('.app-card-open__main')).map(c=>({
      title:c.querySelector('h3 a')?.innerText.trim(),url:c.querySelector('h3 a')?.href,
      type:c.querySelector('[data-test="content-type"]')?.innerText.trim(),
      access:c.querySelector('[data-test="entitlements"]')?.innerText.trim()||null,
      summary:c.innerText.trim().slice(0,1000)
    })).filter(x=>x.title)
  }));
}

export async function sciencePage(tab, query) {
  if (!query?.trim()) throw Error('关键词不能为空');
  await tab.goto('https://www.sciencedirect.com/search?qs=' + encodeURIComponent(query));
  await tab.playwright.locator('.result-item-container').first().waitFor({state:'visible',timeoutMs:25000});
  return await tab.playwright.evaluate(() => ({
    source:'ScienceDirect',
    total:(document.body.innerText.match(/([\d,]+\+?)\s+results/i)||[])[1]||null,
    note:document.body.innerText.includes('only the last three years are included')?'站点提示结果过多，仅包含最近三年；需调整检索条件':null,
    institution:document.body.innerText.includes('Zhejiang University Library')?'Zhejiang University Library':null,
    items:Array.from(document.querySelectorAll('.result-item-container')).map(c=>({
      title:c.querySelector('a.result-list-title-link')?.innerText.trim(),url:c.querySelector('a.result-list-title-link')?.href,
      type:c.querySelector('.article-type')?.innerText.trim()||null,access:c.querySelector('.access-label')?.innerText.trim()||null,
      summary:c.innerText.trim().slice(0,1000)
    })).filter(x=>x.title)
  }));
}

export async function musePage(tab,query) {
  if(!query?.trim()) throw Error('关键词不能为空');
  const p=new URLSearchParams({action:'search',query:'content:'+query+':and',min:'1',max:'10',t:'header'});
  await tab.goto('https://muse.jhu.edu/search?'+p);
  await tab.playwright.locator('#search_results .card_text').first().waitFor({state:'visible',timeoutMs:25000});
  return await tab.playwright.evaluate(()=>({
    source:'Project MUSE',
    institution:document.body.innerText.includes('ACCESS PROVIDED BY ZHEJIANG UNIVERSITY')?'Zhejiang University':null,
    total:(document.body.innerText.match(/([\d,]+)\s+results found/i)||[])[1]||null,
    items:[...document.querySelectorAll('#search_results .card_text')].map(c=>({
      title:c.querySelector('.title h2 a')?.innerText.trim(),url:c.querySelector('.title h2 a')?.href,
      type:c.querySelector('.type')?.innerText.trim(),author:c.querySelector('.author')?.innerText.trim()||null,
      publisher:c.querySelector('.publisher')?.innerText.trim()||null,journal:c.querySelector('.journal')?.innerText.trim()||null,
      access:c.querySelector('.content_access_icon img')?.getAttribute('alt')||null
    })).filter(x=>x.title)
  }));
}

export async function cambridgePage(tab,query) {
  if (!query?.trim()) throw Error('关键词不能为空');
  await tab.goto('https://www.cambridge.org/core/search?q='+encodeURIComponent(query));
  await tab.playwright.locator('ul.details li.title h3 a').first().waitFor({state:'visible',timeoutMs:25000});
  return await tab.playwright.evaluate(()=>({
    source:'Cambridge Core',
    institution:document.body.innerText.includes('Authenticated by\nZhejiang University')?'Zhejiang University':null,
    items:[...document.querySelectorAll('ul.details')].map(c=>({
      title:c.querySelector('li.title h3 a')?.innerText.trim(),url:c.querySelector('li.title h3 a')?.href,
      type:c.querySelector('li.type')?.innerText.trim()||null,authors:c.querySelector('li.author')?.innerText.trim()||null,
      access:c.querySelector('li.status.entitled')?'entitled':c.querySelector('li.status.get')?'get access':null,
      summary:c.innerText.trim().slice(0,1200)
    })).filter(x=>x.title)
  }));
}

// 需注入已在 ProQuest Ebook Central 搜索结果页、完成机构认证的 CUA tab。
// 检查新结果链接中的关键词，防止单页应用异步更新时返回上一轮结果。
export async function ebookCentralPage(tab,query) {
  if(!query?.trim()) throw Error('关键词不能为空');
  await tab.playwright.locator('#ssh_keyword_input').fill(query);
  await tab.playwright.locator('#ssh_keyword_input').press('Enter');
  const encoded=encodeURIComponent(encodeURIComponent(query));
  await tab.playwright.locator('a.pub-list-item-title-link[href*="query='+encoded+'"]').first().waitFor({state:'visible',timeoutMs:25000});
  return await tab.playwright.evaluate(()=>({
    source:'ProQuest Ebook Central',total:(document.body.innerText.match(/([\d,]+)\s+book results/i)||[])[1]||null,
    items:[...document.querySelectorAll('.pub-list-item-description')].map(c=>({
      title:c.querySelector('.pub-list-item-title-link')?.innerText.trim(),url:c.querySelector('.pub-list-item-title-link')?.href,
      authors:[...c.querySelectorAll('.auth-meta-link')].map(a=>a.innerText.trim()),publisher:c.querySelector('.meta-publisher-link')?.innerText.trim()||null,
      year:c.querySelector('.meta-pub-year')?.innerText.trim()||null,isbn:[...c.querySelectorAll('.pub-meta-pisbn-value,.pub-meta-eisbn-value')].map(x=>x.innerText.trim()),
      access:c.querySelector('.pub-availability-status')?.innerText.trim()||null
    })).filter(x=>x.title)
  }));
}

export async function naturePage(tab,query) {
  if(!query?.trim()) throw Error('关键词不能为空');
  await tab.goto('https://www.nature.com/search?q='+encodeURIComponent(query));
  await tab.playwright.locator('article.c-card h3 a').first().waitFor({state:'visible',timeoutMs:20000});
  return await tab.playwright.evaluate(()=>({
    source:'Nature',total:(document.body.innerText.match(/([\d,]+) results/i)||[])[1]||null,
    items:[...document.querySelectorAll('article.c-card')].map(c=>({
      title:c.querySelector('h3 a')?.innerText.trim(),url:c.querySelector('h3 a')?.href,
      authors:[...c.querySelectorAll('[data-test="author-list"] [itemprop="name"]')].map(x=>x.innerText.trim()),
      type:c.querySelector('[data-test="article.type"]')?.innerText.trim()||null,
      access:c.querySelector('[data-test="open-access"]')?.innerText.trim()||null,
      date:c.querySelector('time')?.getAttribute('datetime')||null,
      journal:c.querySelector('[data-test="journal-title-and-link"]')?.innerText.trim()||null,
      summary:c.querySelector('[data-test="article-description"]')?.innerText.trim()||null
    })).filter(x=>x.title)
  }));
}

export async function emeraldPage(tab,query) {
  if(!query?.trim()) throw Error('关键词不能为空');
  await tab.goto('https://www.emerald.com/insight/search-results?page=1&q='+encodeURIComponent(query)+'&SearchSourceType=1');
  await tab.playwright.locator('.sr-list .sri-title a').first().waitFor({state:'visible',timeoutMs:25000});
  return await tab.playwright.evaluate(()=>({
    source:'Emerald Insight',total:(document.body.innerText.match(/1-20 of\s*([\d,]+)/i)||[])[1]||null,
    items:[...document.querySelectorAll('.sr-list')].map(c=>({
      title:c.querySelector('.sri-title a')?.innerText.trim(),url:c.querySelector('.sri-title a')?.href,
      type:c.querySelector('.sri-type')?.innerText.trim()||null,summary:c.querySelector('.item-info')?.innerText.trim().slice(0,1200)||null
    })).filter(x=>x.title)
  }));
}

export async function sagePage(tab,query) {
  if(!query?.trim()) throw Error('关键词不能为空');
  const p=new URLSearchParams({'fields[0].lo':'and','fields[0].f':'all','fields[0].val':query});
  await tab.goto('https://sage.cnpereading.com/doSearch?'+p);
  await tab.playwright.locator('[class*="ArticlesResultItem_resultItem"] h2 a').first().waitFor({state:'visible',timeoutMs:25000});
  return await tab.playwright.evaluate(()=>({
    source:'SAGE（易阅通）',institution:document.body.innerText.includes('Zhejiang Library')?'Zhejiang Library':null,
    total:(document.body.innerText.match(/共\s*((?:\d{1,3}(?:,\d{3})+|\d+))\s*条结果/)?.[1]?.replaceAll(',',''))??null,
    items:[...document.querySelectorAll('[class*="ArticlesResultItem_resultItem"]')].map(c=>({
      title:c.querySelector('h2 a')?.innerText.trim(),url:c.querySelector('h2 a')?.href,
      type:c.querySelector('[class*="ArticlesResultItem_articleType"]')?.innerText.trim()||null,
      authors:c.querySelector('[class*="ArticlesResultItem_authors__"]')?.innerText.trim()||null,
      access:c.querySelector('[class*="ArticlesResultItem_accessLabel"]')?.innerText.trim()||null,
      date:c.querySelector('[class*="ArticlesResultItem_publishDate"]')?.innerText.trim()||null
    })).filter(x=>x.title)
  }));
}

export async function bmjPage(tab,query) {
  if(!query?.trim()) throw Error('关键词不能为空');
  await tab.goto('https://journals.bmj.com/search');
  await tab.playwright.getByRole('textbox',{name:'Search Term',exact:true}).fill(query);
  await tab.playwright.locator('#edit-button').click();
  await tab.playwright.locator('.highwire-search-results .highwire-cite-linked-title').first().waitFor({state:'visible',timeoutMs:20000});
  return await tab.playwright.evaluate(()=>({
    source:'BMJ Journals',total:(document.body.innerText.match(/([\d,]+) results/)||[])[1]||null,
    items:[...document.querySelectorAll('.highwire-search-results .highwire-article-citation')].map(c=>({
      title:c.querySelector('.highwire-cite-linked-title')?.innerText.trim(),url:c.querySelector('.highwire-cite-linked-title')?.href,
      authors:c.querySelector('.highwire-cite-authors')?.innerText.trim()||null,journal:c.querySelector('.highwire-cite-metadata-journal')?.innerText.trim()||null,
      date:c.querySelector('.highwire-cite-metadata-date')?.innerText.trim()||null,doi:c.querySelector('.highwire-cite-metadata-doi')?.innerText.trim()||null,
      summary:c.querySelector('.highwire-cite-snippet')?.innerText.trim()||null
    })).filter(x=>x.title)
  }));
}

export async function annualReviewsPage(tab,query) {
  if(!query?.trim()) throw Error('关键词不能为空');
  await tab.goto('https://www.annualreviews.org/search?value1='+encodeURIComponent(query)+'&option1=fulltext');
  await tab.playwright.locator('.resultItemContainer__meta-data h2 a').first().waitFor({state:'visible',timeoutMs:25000});
  return await tab.playwright.evaluate(()=>({
    source:'Annual Reviews',institution:document.body.innerText.includes('Access provided by: Zhejiang University')?'Zhejiang University':null,
    total:(document.body.innerText.match(/\d+\s*-\s*\d+\s+of\s+([\d,]+)\s+for/i)||[])[1]||null,
    items:[...document.querySelectorAll('.resultItemContainer__meta-data')].map(c=>({
      title:c.querySelector('h2 a')?.innerText.trim(),url:c.querySelector('h2 a')?.href,
      authors:[...c.querySelectorAll('.author-list__item a')].map(x=>x.innerText.trim()),
      publication:c.querySelector('.source')?.innerText.trim()||null,date:c.querySelector('.Type-PubDate')?.innerText.trim()||null,
      type:c.querySelector('.Type-Publication')?.innerText.trim()||null,summary:c.querySelector('.js-desc')?.innerText.trim()||null
    })).filter(x=>x.title)
  }));
}

export async function bioonePage(tab,query) {
  if(!query?.trim()) throw Error('关键词不能为空');
  await tab.goto('https://bioone.org/search?term='+encodeURIComponent(query));
  await tab.playwright.locator('.TOCLineItemRowCol1 .ProfileTOCLineItemBoldText').first().waitFor({state:'visible',timeoutMs:25000});
  return await tab.playwright.evaluate(()=>({
    source:'BioOne',total:(document.body.innerText.match(/([\d,]+) results found for/i)||[])[1]||null,
    items:[...document.querySelectorAll('.TOCLineItemRowCol1')].map(c=>({
      title:c.querySelector('.ProfileTOCLineItemBoldText')?.innerText.trim(),url:c.querySelector('.ProfileTOCLineItemBoldText')?.closest('a')?.href,
      author:c.querySelector('.TOCLineItemText2')?.innerText.trim()||null,date:c.querySelector('.ProfileTocLineItemTitleText')?.innerText.trim()||null,
      publication:c.querySelector('.citation-content')?.innerText.trim()||null
    })).filter(x=>x.title)
  }));
}

export async function hepJournalsPage(tab,query) {
  if(!query?.trim()) throw Error('关键词不能为空');
  await tab.goto('https://journal.hep.com.cn/hep/EN/searchresult?keyword='+encodeURIComponent(query));
  await tab.playwright.locator('#article_list_container li.article_detail_tmp a.article_detail_title').first().waitFor({state:'visible',timeoutMs:25000});
  return await tab.playwright.evaluate(()=>({
    source:'HEP Journals（高等教育出版社）',
    items:[...document.querySelectorAll('#article_list_container li.article_detail_tmp')].filter(c=>c.getClientRects().length).map(c=>({
      title:c.querySelector('a.article_detail_title')?.innerText.trim(),url:c.querySelector('a.article_detail_title')?.href,
      authors:c.querySelector('.article_detail_author')?.innerText.trim()||null,journal:c.querySelector('.article_detail_journal_name')?.innerText.trim()||null,
      citation:c.querySelector('.article_detail_issue')?.innerText.trim()||null,doi:c.querySelector('.article_detail_doi')?.href||null
    })).filter(x=>x.title)
  }));
}

export async function euclidPage(tab,query) {
  if(!query?.trim()) throw Error('关键词不能为空');
  await tab.goto('https://projecteuclid.org/search?term='+encodeURIComponent(query));
  await tab.playwright.locator('.TOCLineItemRowCol1 .ProfileTOCLineItemBoldText').first().waitFor({state:'visible',timeoutMs:25000});
  return await tab.playwright.evaluate(()=>({
    source:'Project Euclid',total:(document.body.innerText.match(/([\d,]+) results found for/i)||[])[1]||null,
    items:[...document.querySelectorAll('.TOCLineItemRowCol1')].map(c=>({
      title:c.querySelector('.ProfileTOCLineItemBoldText')?.innerText.trim(),url:c.querySelector('.ProfileTOCLineItemBoldText')?.closest('a')?.href,
      author:c.querySelector('.TOCLineItemText2')?.innerText.trim()||null,date:c.querySelector('.ProfileTocLineItemTitleText')?.innerText.trim()||null,
      publication:c.querySelector('.citation-content')?.innerText.trim()||null
    })).filter(x=>x.title)
  }));
}

export async function scoap3BooksPage(tab,query) {
  if(!query?.trim()) throw Error('关键词不能为空');
  await tab.goto('https://scoap3.org/scoap3-books/');
  await tab.playwright.locator('#dt-search-0').fill(query);
  return await tab.playwright.evaluate(()=>({
    source:'SCOAP3 Books',info:document.querySelector('#tablepress-21_info')?.textContent?.trim()||null,
    items:[...document.querySelectorAll('#tablepress-21 tbody tr')].map(r=>{
      const c=r.querySelectorAll('td');
      return {title:c[0]?.innerText.trim(),url:c[0]?.querySelector('a')?.href||null,authors:c[1]?.innerText.trim()||null,publisher:c[2]?.innerText.trim()||null};
    }).filter(x=>x.url)
  }));
}

export async function britannicaPage(tab,query) {
  if(!query?.trim()) throw Error('关键词不能为空');
  await tab.goto('https://academic.eb.cnpereading.com/levels/collegiate/search/articles?query='+encodeURIComponent(query));
  return await tab.playwright.evaluate(()=>({
    source:'Britannica Academic',total:(document.body.innerText.match(/Displaying\s+\d+\s*-\s*\d+\s+of\s+([\d,]+)\s+results/i)||[])[1]||null,
    items:[...document.querySelectorAll('a.primary-article-link')].filter(a=>a.closest('li')?.querySelector('a.primary-article-link')===a).map(a=>({
      title:a.innerText.trim(),url:a.href,summary:a.closest('li')?.querySelector(':scope > p')?.innerText.trim()||null
    }))
  }));
}

export async function scoap3ArticlesPage(tab,query) {
  if(!query?.trim()) throw Error('关键词不能为空');
  await tab.goto('https://repo.scoap3.org/search?search_simple_query_string='+encodeURIComponent(query));
  let ready=false;
  for(let i=0;i<50;i++) {
    ready=await tab.playwright.evaluate(()=>{
      const m=document.body.innerText.match(/Found\s+([\d,]+)\s+results/i);
      if(!m) return false;
      return document.querySelectorAll('.search-results-record').length>=Math.min(10,Number(m[1].replace(/,/g,'')));
    });
    if(ready) break;
    await new Promise(resolve=>setTimeout(resolve,300));
  }
  if(!ready) throw Error('SCOAP3 检索页面未完整加载，请稍后重试');
  return await tab.playwright.evaluate(()=>({
    source:'SCOAP3 Repository',total:(document.body.innerText.match(/Found\s+([\d,]+)\s+results/i)||[])[1]||null,
    items:[...document.querySelectorAll('.search-results-record')].map(c=>({
      title:c.querySelector('a[href^="/records/"]')?.innerText.trim(),url:c.querySelector('a[href^="/records/"]')?.href,
      authors:c.querySelector('.search-authors')?.innerText.trim()||null,date:c.querySelector('.search-results-record-date')?.innerText.replace(/^\s*-\s*/,'').trim()||null,
      doi:c.querySelector('a[href^="https://doi.org/"]')?.href||null,arxiv:c.querySelector('a[href^="https://arxiv.org/abs/"]')?.href||null
    })).filter(x=>x.title)
  }));
}

// Caller must open Ovid's Zhejiang University LWW journal-browse screen first.
// Returned data deliberately excludes session-bearing URLs.
export async function ovidJournalPage(tab,query) {
  if(!query?.trim()) throw Error('关键词不能为空');
  const before=await tab.playwright.evaluate(()=>JSON.stringify([...document.querySelectorAll('.journalname')].map(c=>c.querySelector('h2 a')?.innerText.trim()).filter(Boolean)));
  await tab.playwright.getByRole('combobox',{name:'期刊名称'}).fill(query);
  await tab.playwright.getByRole('button',{name:'检索',exact:true}).click();
  for(let i=0;i<50;i++) {
    const items=await tab.playwright.evaluate(()=>[...document.querySelectorAll('.journalname')].map(c=>({title:c.querySelector('h2 a')?.innerText.trim(),details:c.getAttribute('title')})).filter(x=>x.title));
    if(items.length && JSON.stringify(items.map(x=>x.title))!==before && items.every(x=>x.title.toLowerCase().includes(query.trim().toLowerCase())))
      return {source:'Ovid 浙大期刊列表',experimental:true,items};
    await new Promise(resolve=>setTimeout(resolve,300));
  }
  throw Error('无法确认 Ovid 结果已更新；重复查询、零结果或非字面匹配均需手动核对');
}

export async function smfPage(tab,query) {
  if(!query?.trim()) throw Error('关键词不能为空');
  await tab.goto('https://smf.emath.fr/les-publications?search='+encodeURIComponent(query));
  return await tab.playwright.evaluate(()=>({
    source:'Société Mathématique de France',count:document.querySelector('.view__results_count')?.innerText.trim()||null,
    items:[...document.querySelectorAll('a.publication')].map(a=>({
      title:a.querySelector('.publication__title')?.innerText.trim(),url:a.href,
      authors:a.querySelector('.publication__text')?.innerText.trim()||null,
      collection:a.querySelector('.publication__collection')?.innerText.trim()||null,
      citation:a.querySelector('.publication__more_info')?.innerText.trim()||null
    })).filter(x=>x.title)
  }));
}

export async function emsPage(tab,query) {
  if(!query?.trim()) throw Error('关键词不能为空');
  await tab.goto('https://ems.press/search?term='+encodeURIComponent(query));
  await tab.playwright.locator('li.result-item h2').first().waitFor({state:'visible',timeoutMs:20000});
  return await tab.playwright.evaluate(()=>({
    source:'EMS Press（Google Search）',items:[...document.querySelectorAll('li.result-item')].map(c=>({
      title:c.querySelector('h2')?.innerText.trim(),url:c.querySelector('h2')?.closest('a')?.href,
      type:c.querySelector('.resource-type')?.innerText.trim()||null,snippet:c.querySelector('p')?.innerText.trim()||null
    })).filter(x=>x.title)
  }));
}

export async function sageMethodsPage(tab,query) {
  if(!query?.trim()) throw Error('关键词不能为空');
  await tab.goto('https://methods.sagepub.com/');
  await tab.playwright.getByRole('searchbox',{name:'Search within Sage Research Methods'}).fill(query);
  await tab.playwright.getByRole('button',{name:'run search'}).click();
  await tab.playwright.locator('.sage-card--search-result__title a').first().waitFor({state:'visible',timeoutMs:30000});
  return await tab.playwright.evaluate(()=>({
    source:'Sage Research Methods',institution:document.body.innerText.includes('Zhejiang Library')?'Zhejiang Library':null,
    total:(document.body.innerText.match(/([\d,]+) results found/)||[])[1]||null,
    items:[...document.querySelectorAll('.sage-card--search-result')].map(c=>({
      title:c.querySelector('.sage-card--search-result__title a')?.innerText.trim(),url:c.querySelector('.sage-card--search-result__title a')?.href,
      type:c.querySelector('.sage-card--search-result__content-type-heading')?.innerText.trim()||null
    })).filter(x=>x.title)
  }));
}

export async function iceGeotechniquePage(tab,query) {
  if(!query?.trim()) throw Error('关键词不能为空');
  await tab.goto('https://www.emerald.com/jgeot/search-results?page=1&q='+encodeURIComponent(query)+'&fl_SiteID=1000521');
  await tab.playwright.locator('.sr-list .sri-title h4 a').first().waitFor({state:'visible',timeoutMs:25000});
  return await tab.playwright.evaluate(()=>({
    source:'ICE Publishing — Géotechnique',total:(document.body.innerText.match(/1\s*[-–]\s*\d+\s+of\s+([\d,]+)/i)||[])[1]||null,
    items:[...document.querySelectorAll('.sr-list')].map(c=>({
      title:c.querySelector('.sri-title h4 a')?.innerText.trim(),url:c.querySelector('.sri-title h4 a')?.href,
      authors:[...c.querySelectorAll('.sri-authors a')].map(x=>x.innerText.trim()),
      citation:c.querySelector('.al-citation-list')?.innerText.trim()||null,doi:c.querySelector('a[href^="https://doi.org/"]')?.href||null,
      availability:c.querySelector('.sri-title [aria-label]')?.getAttribute('aria-label')||null
    })).filter(x=>x.title)
  }));
}

export async function jovePage(tab,query) {
  if(!query?.trim()) throw Error('关键词不能为空');
  const q=encodeURIComponent(query);
  await tab.goto('https://www.jove.com/search?query='+q+'&content_type=&page=1&originalQuery='+q+'&override_query=true');
  await tab.playwright.locator('.search-result-card-title-link').first().waitFor({state:'visible',timeoutMs:30000});
  return await tab.playwright.evaluate(()=>({
    source:'JoVE',summary:[...document.querySelectorAll('p')].map(p=>p.innerText).find(t=>t.includes('Showing results'))||null,
    items:[...document.querySelectorAll('.search-result-card-content')].map(c=>({
      title:c.querySelector('.search-result-card-title-link')?.innerText.trim(),url:c.querySelector('.search-result-card-title-link')?.href,
      type:c.querySelector('.search-result-card-tag-text')?.innerText.trim()||null,year:c.querySelector('.search-result-card-info-year')?.innerText.trim()||null,
      availability:c.querySelector('.search-result-card-access-indicator')?.innerText.trim()||null
    })).filter(x=>x.title)
  }));
}

export async function tairGenePage(tab,query) {
  if(!query?.trim()) throw Error('关键词不能为空');
  await tab.goto('https://www.arabidopsis.org/results?mainType=general&searchText='+encodeURIComponent(query)+'&category=genes');
  await tab.playwright.locator('main table[aria-busy="false"] tbody tr a').first().waitFor({state:'visible',timeoutMs:25000});
  return await tab.playwright.evaluate(()=>({
    source:'TAIR gene search',status:[...document.querySelectorAll('[role="status"]')].map(e=>e.innerText.trim()).find(t=>t.includes('matches'))||null,
    items:[...document.querySelectorAll('main table tbody tr')].map(r=>({
      locus:r.querySelector('a')?.innerText.trim(),url:r.querySelector('a')?.href,description:r.querySelectorAll('td')[3]?.innerText.trim()||null
    })).filter(x=>x.locus)
  }));
}

export async function opticaPage(tab,query) {
  if(!query?.trim()) throw Error('关键词不能为空');
  await tab.goto('https://opg.optica.org/search.cfm?q='+encodeURIComponent(query)+'&ibsearch=false');
  await tab.playwright.locator('li.sr-item .sri-title a').first().waitFor({state:'visible',timeoutMs:30000});
  return await tab.playwright.evaluate(()=>({
    source:'Optica Publishing Group',note:'openAccess 为 true 表示页面存在开放获取图标；null 表示未发现图标，具体权限须查原文。',total:(document.body.innerText.match(/(?:^|\s)((?:\d{1,3}(?:,\d{3})+|\d+)) results \(filtered\)/)?.[1]?.replaceAll(',',''))??null,
    items:[...document.querySelectorAll('li.sr-item')].map(c=>({
      title:c.querySelector('.sri-title a')?.innerText.trim(),url:c.querySelector('.sri-title a')?.href,
      authors:c.querySelector('.sri-authors')?.innerText.trim()||null,year:c.querySelector('.sri-year')?.innerText.trim()||null,
      citation:c.querySelector('.sri-journal')?.innerText.replace(/View:.*/,'').trim()||null,
      openAccess:c.querySelector('img[alt="open access"]')?true:null
    })).filter(x=>x.title)
  }));
}

export async function crcHandbookDocumentsPage(tab,query) {
  if(!query?.trim()) throw Error('关键词不能为空');
  await tab.goto('https://libdb.zju.edu.cn/s/lib/libtb/turning/425');
  await tab.playwright.getByRole('textbox',{name:'Search Terms'}).fill(query);
  await tab.playwright.getByRole('button',{name:'Search',exact:true}).click();
  let ready=false;
  for(let i=0;i<80;i++) {
    ready=await tab.playwright.evaluate(q=>document.querySelector('#ResultsCard .ui-card-title')?.innerText.includes("'"+q+"'")||false,query);
    if(ready) break;
    await new Promise(resolve=>setTimeout(resolve,300));
  }
  if(!ready) throw Error('未确认 CRC 手册检索结果');
  return await tab.playwright.evaluate(()=>({
    source:'CRC Handbook of Chemistry and Physics',sections:[...document.querySelectorAll('#resultsForm [role="tab"]')].map(h=>({
      section:h.innerText.trim(),items:[...h.nextElementSibling.querySelectorAll('tr[role="row"] td[role="gridcell"]')].map(c=>({
        title:c.querySelector('span[style*="font-weight"]')?.innerText.trim(),
        pages:[...c.querySelectorAll('a')].map(a=>a.innerText.trim()).filter(x=>/^\d+$/.test(x))
      })).filter(x=>x.title)
    }))
  }));
}

export async function amsBooksPage(tab,query) {
  if(!query?.trim()) throw Error('关键词不能为空');
  await tab.goto('https://libdb.zju.edu.cn/s/lib/libtb/turning/2043');
  await tab.goto('https://ebookcentral.proquest.com/ebc/lib/zhejiang/#/search?query='+encodeURIComponent(query)+'&op=advance&publisher=American%20Mathematical%20Society');
  const enc=encodeURIComponent(encodeURIComponent(query));
  let ready=false;
  for(let i=0;i<80;i++) {
    ready=await tab.playwright.evaluate(q=>document.body.innerText.includes('PUBLISHERAmerican Mathematical Society') && [...document.querySelectorAll('a.pub-list-item-title-link')].some(a=>a.href.includes('query='+q)),enc);
    if(ready) break;
    await new Promise(resolve=>setTimeout(resolve,300));
  }
  if(!ready) throw Error('未确认数学会出版社筛选及关键词');
  return await tab.playwright.evaluate(()=>({
    source:'AMS ebooks via ProQuest',total:(document.body.innerText.match(/([\d,]+)\s+book results/i)||[])[1]||null,
    items:[...document.querySelectorAll('.pub-list-item-description')].map(c=>({
      title:c.querySelector('.pub-list-item-title-link')?.innerText.trim(),url:c.querySelector('.pub-list-item-title-link')?.href,
      authors:[...c.querySelectorAll('.auth-meta-link')].map(a=>a.innerText.trim()),publisher:c.querySelector('.meta-publisher-link')?.innerText.trim()||null,
      year:c.querySelector('.meta-pub-year')?.innerText.trim()||null,isbn:[...c.querySelectorAll('.pub-meta-pisbn-value,.pub-meta-eisbn-value')].map(x=>x.innerText.trim()),
      access:c.querySelector('.pub-availability-status')?.innerText.trim()||null
    })).filter(x=>x.title)
  }));
}

export async function ldcCatalogPage(tab,query) {
  if(!query?.trim()) throw Error('关键词不能为空');
  await tab.goto('https://catalog.ldc.upenn.edu/search');
  await tab.playwright.locator('input[name="q[name_cont]"]').fill(query);
  await tab.playwright.getByRole('button',{name:'Search Catalog'}).click();
  await tab.playwright.getByRole('heading',{name:'Catalog Search Results'}).waitFor({state:'visible',timeoutMs:20000});
  return await tab.playwright.evaluate(()=>({
    source:'LDC Catalog',items:[...document.querySelectorAll('table tr')].map(r=>({
      code:r.querySelector('td:first-child a')?.innerText.trim(),url:r.querySelector('td:first-child a')?.href,
      title:r.querySelector('td:nth-child(2)')?.innerText.trim()
    })).filter(x=>x.code&&x.title)
  }));
}

export async function bloomsburyPage(tab,query) {
  if(!query?.trim()) throw Error('关键词不能为空');
  await tab.goto('https://www.bloomsburycollections.com/search-results?any='+encodeURIComponent(query));
  await tab.playwright.locator('a.search-result-link.search-title').first().waitFor({state:'visible',timeoutMs:30000});
  return await tab.playwright.evaluate(()=>({
    source:'Bloomsbury Collections',summary:(document.body.innerText.match(/Showing results\s+[^\n]+/)||[])[0]||null,
    items:[...document.querySelectorAll('a.search-result-link.search-title')].map(a=>({
      title:a.getAttribute('aria-label')||a.innerText.trim(),url:a.href,
      authors:[...a.closest('h4').querySelectorAll('.search-author')].map(e=>e.innerText.trim())
    })).filter(x=>x.title)
  }));
}

export async function medonePage(tab,query) {
  if(!query?.trim()) throw Error('关键词不能为空');
  await tab.goto('https://medone-education.thieme.com/search;;searchterm='+encodeURIComponent(query));
  await tab.playwright.locator('main a[href*="fromSearch=true"]').first().waitFor({state:'visible',timeoutMs:30000});
  return await tab.playwright.evaluate(()=>({
    source:'Thieme MedOne Education',notice:(document.body.innerText.match(/[^\n]*non-licensed packages[^\n]*/i)||[])[0]||null,
    items:[...document.querySelectorAll('main a[href*="fromSearch=true"]')].map(a=>({
      title:(a.querySelector('.subtitle,.title')?.innerText||a.innerText).trim(),url:a.href,
      details:[...a.querySelectorAll('.info')].map(x=>x.innerText.trim())
    })).filter(x=>x.title)
  }));
}
