/** One institution-session search, reading only visible image identifiers and caption snippets. */
export async function gongyuanImageSearch(tab,keyword,submitSearch,limit=3){
 if(typeof keyword!=='string'||!keyword.trim()||keyword.length>100||typeof submitSearch!=='function'||!Number.isInteger(limit)||limit<1||limit>10)throw Error('需要关键词、单次检索回调及1–10条上限');
 await submitSearch();
 let data; for(let attempt=0;attempt<20;attempt++){
 data=await tab.playwright.evaluate(()=>({host:location.hostname,path:location.pathname,text:document.body.innerText,rows:[...document.querySelectorAll('a[href*="image.php?type=detail&id="]')].map(a=>({href:a.getAttribute('href'),caption:a.closest('table')?.parentElement?.closest('table')?.querySelector('font.f')?.innerText||''}))}));
 if(data.text.includes('含有"'+keyword.trim()+'"的结果') && data.rows.length)break;
 await new Promise(resolve=>setTimeout(resolve,200));
 }
 if(data.host!=='10.15.61.245'||data.path!=='/search.php')throw Error('不是浙大教学图片库结果页');
 if(!data.text.includes('含有"'+keyword.trim()+'"的结果'))throw Error('页面检索词不一致');
 const match=data.text.match(/共\s*(\d+)\s*项\s*(\d+)\s*页/);if(!match)throw Error('无法识别结果数量');
 const items=data.rows.slice(0,limit).map(x=>{let m=x.href?.match(/^image\.php\?type=detail&id=(\d+)$/);if(!m||!x.caption.trim())throw Error('图片编号或说明缺失');return {id:m[1],caption_snippet:x.caption.trim()}});
 return {source:'公元集成教学图片数据库（浙大会话）',query:keyword.trim(),total:Number(match[1]),pages:Number(match[2]),items,note:'一次结果首屏的图片编号和页面截断说明；不复制图片，全文说明、分页及用途范围未验证。'};
}
