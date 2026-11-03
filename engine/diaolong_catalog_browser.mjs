/** 读取已登录雕龙日本古典书籍库当前目录页题录。 */
export async function diaolongCatalog(tab){
 const d=await tab.playwright.evaluate(()=>{const u=new URL(location.href),t=document.body.innerText,m=t.match(/共\s*([\d,]+)\s*種\s*\/\s*([\d,]+)\s*卷.*?第\s*(\d+)\s*\/\s*(\d+)\s*頁/s);let rows=[...document.querySelectorAll('#bsa01 td[class^="singlerecord_"]')].map(e=>({title:e.querySelector('.TI a')?.innerText.trim()||null,collection:e.querySelector('.SK')?.innerText.trim()||null,authorEdition:e.querySelector('.AU')?.innerText.trim()||null})).filter(x=>x.title);return {host:u.hostname,path:u.pathname,institution:t.includes('浙江大學'),total:m?Number(m[1].replaceAll(',','')):null,volumes:m?Number(m[2].replaceAll(',','')):null,page:m?Number(m[3]):null,pages:m?Number(m[4]):null,rows};});
 if(d.host!=='tk.cepiec.com.cn'||d.path!=='/ancientc/ancientkm'||!d.institution||!d.total||!d.rows.length)throw Error('当前标签不是已登录日本古典书籍库的目录结果页');
 return {source:'雕龙日本古典书籍库',totalKinds:d.total,totalVolumes:d.volumes,page:d.page,pages:d.pages,items:d.rows,note:'当前机构会话目录页题录；书种与首页显示书数口径可能不同，未核对。'};
}
