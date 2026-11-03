/** 漢達文庫傳世快速檢索：僅回傳少量書目位置，復用已授權的瀏覽器。 */
export async function chantSearch(tab, query, limit=5) {
 if (typeof query !== 'string' || !/^[\p{L}\p{N}]{1,30}$/u.test(query)) throw Error('查詢詞須為 1–30 個文字或數字，不含空白或控制字元');
 if (!Number.isInteger(limit) || limit<1 || limit>10) throw Error('limit 須為 1–10');
 const initial=await tab.playwright.domSnapshot();
 if(!initial.includes('[Zhejiang University]') || !initial.includes('傳世') || !initial.includes('輸入文字檢索')) throw Error('未識別浙大機構檢索頁；請確認校園 IP 及試用授權');
 await tab.playwright.getByRole('textbox',{name:'輸入文字檢索'}).last().pressSequentially(query);
 await tab.playwright.getByRole('button',{name:''}).click();
 await tab.playwright.getByRole('heading',{name:'【'+query+'】'}).waitFor({state:'visible',timeoutMs:20000});
 const d=await tab.playwright.evaluate((max)=>{
  const text=document.body.innerText.slice(0,2500), heading=document.querySelector('h3')?.innerText || '';
  const hits=[...document.querySelectorAll('h5')].slice(0,max).map(h=>({location:h.innerText.trim(),links:[...h.querySelectorAll('a[href]')].slice(0,2).map(a=>({title:a.innerText.trim(),url:a.href}))}));
  return {url:location.href,heading,text,hits};
 },limit);
 if(!d.url.startsWith('https://www.chant.org/result/FastSearch/') || d.heading!=='【'+query+'】' || !d.text.includes('[Zhejiang University]')) throw Error('結果詞或機構身份未確認');
 const total=d.text.match(/結果總數：\s*([\d,]+)/), books=d.text.match(/共\s*([\d,]+)\s*書目/);
 if(!total || !books) throw Error('未確認结果总数和书目数；零结果或站点变更未验证');
 return {source:'漢達文庫，校園 IP 試用',query,scope:'傳世',institution:'Zhejiang University',matched_hits:Number(total[1].replaceAll(',','')),matched_books:Number(books[1].replaceAll(',','')),items:d.hits,source_url:d.url,note:'仅返回最多 10 个书目位置，不返回正文；一次人工等效查询。未确认自动化或 AI 利用许可、全文和其他子库权限。'};
}
