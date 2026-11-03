/** 漢達快速檢索；零結果不等於機構身份失效。未自動轉換簡繁。 */
export async function chantSearch(tab, query, limit=5) {
 if (typeof query !== 'string' || !/^[\p{L}\p{N}]{1,30}$/u.test(query)) throw Error('查詢詞須為 1–30 個文字或數字');
 if (!Number.isInteger(limit) || limit<1 || limit>10) throw Error('limit 須為 1–10');
 const initial=await tab.playwright.domSnapshot();
 if(!initial.includes('[Zhejiang University]') || !initial.includes('輸入文字檢索')) throw Error('未識別浙大機構檢索頁');
 await tab.playwright.getByRole('textbox',{name:'輸入文字檢索'}).last().fill(query);
 await tab.playwright.getByRole('button',{name:''}).click();
 let d;
 for(let attempt=0;attempt<40;attempt++) {
  d=await tab.playwright.evaluate((max)=>{
   const text=document.body.innerText;
   const headings=[...document.querySelectorAll('h1,h2,h3')].map(h=>h.innerText.trim()).filter(t=>/^【.*】$/.test(t));
   return {url:location.href,title:document.title,headings,identity:text.includes('[Zhejiang University]'),
    hits:text.match(/結果總數[：:]\s*([\d,]+)/)?.[1],books:text.match(/共\s*([\d,]+)\s*書目/)?.[1],
    explicitEmpty:[...document.querySelectorAll('script:not([src])')].some(s=>/ShowErrorMessage\(\s*(["'])沒有結果\1\s*,\s*(["'])info\2\s*\)/.test(s.textContent)),
    locations:[...document.querySelectorAll('h5')].slice(0,max).map(h=>({location:h.innerText.trim(),links:[...h.querySelectorAll('a[href]')].slice(0,2).map(a=>({title:a.innerText.trim(),url:a.href}))}))};
  },limit);
  if(d.url.startsWith('https://www.chant.org/result/FastSearch/')) break;
  await new Promise(resolve=>setTimeout(resolve,250));
 }
 const u=new URL(d.url);
 if(u.origin!=='https://www.chant.org' || decodeURIComponent(u.pathname)!=='/result/FastSearch/'+query || !d.identity || (d.title!=='漢達文庫 - 檢索結果 - '+query && !d.headings.includes('【'+query+'】')) || d.headings.some(h=>h!=='【'+query+'】')) throw Error('結果詞或機構身份未確認');
 const total=d.hits===undefined?null:Number(d.hits.replaceAll(',','')), books=d.books===undefined?null:Number(d.books.replaceAll(',',''));
 if(d.explicitEmpty && (total>0 || books>0 || d.locations.length))throw Error('零結果提示與記錄矛盾');
 if((total===0 && books!==0 && books!==null)||(books===0 && total!==0 && total!==null)||(total===0 && d.locations.length))throw Error('結果計數矛盾');
 const empty=(total===0 && books===0 && !d.locations.length) || d.explicitEmpty && !d.locations.length && (total===null || total===0) && (books===null || books===0);
 if(!empty && (total===null || books===null || !d.locations.length)) throw Error('結果結構未確認，不能從缺少h3推定零結果');
 const uuid='[0-9a-fA-F]{8}(?:-[0-9a-fA-F]{4}){3}-[0-9a-fA-F]{12}';
 const items=d.locations.map(item=>{
  const refs=item.links.map(link=>{const v=new URL(link.url),m=v.pathname.match(new RegExp('^/text/book/('+uuid+')(?:/('+uuid+'))?/?$'));if(v.origin!=='https://www.chant.org'||v.search||v.hash||!m||!link.title)throw Error('書目鏈接未確認');return {book:m[1],chapter:m[2],title:link.title};});
  if(!refs.length||refs[0].chapter)throw Error('缺少書目鏈接');
  const out={...item,book_id:refs[0].book,book_title:refs[0].title};
  if(refs[1]?.chapter){if(refs[1].book!==refs[0].book)throw Error('章節與書目不一致');Object.assign(out,{chapter_id:refs[1].chapter,chapter_title:refs[1].title});}return out;
 });
 return {source:'漢達文庫',query,institution:'Zhejiang University',matched_hits:empty?0:total,matched_books:empty?0:books,items,source_url:d.url,empty_result:empty,note:'僅當前查詢的書目位置；不自動改寫檢索詞，分組篩選及整庫正文權限未確認。'};
}
