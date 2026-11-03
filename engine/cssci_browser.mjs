/* CSSCI 来源文献篇名检索：当前页题录，不访问全文。 */
export async function cssciSearch(tab,keyword){
 if(typeof keyword!=='string'||!keyword.trim()||keyword.length>100)throw Error('关键词需为 1–100 字');
 const q=keyword.trim(), u=new URL('https://cssci.nju.edu.cn/ly_search_view.html');
 u.search=new URLSearchParams({title:`${q}   1   AND|||`,start_year:'1998',end_year:String(new Date().getFullYear()),nian:'',juan:'',qi:'',xw1:'',xw2:'',wzlx:'',xkfl1:'',jj:'',pagenum:'20',order_type:'nian',order_px:'DESC'}).toString();
 await tab.goto(u.toString());
 try{await tab.playwright.locator('#show_table_content tr').nth(1).waitFor({state:'visible',timeoutMs:20000});}catch{throw Error('未读取题录；请检查是否无结果、验证、登录或页面变化。');}
 const data=await tab.playwright.evaluate(()=>({institution:document.querySelector('#user_login_message')?.innerText.includes('浙江大学')?'浙江大学':null,items:[...document.querySelectorAll('#show_table_content tr')].slice(1).filter(r=>r.getClientRects().length).map(r=>{let c=r.querySelectorAll('td'),a=c[2]?.querySelector('a');return {authors:c[1]?.innerText.trim().split('/').map(x=>x.trim()).filter(Boolean),title:a?.innerText.trim(),englishTitle:a?.getAttribute('title')||null,journal:c[3]?.innerText.trim(),issue:c[4]?.innerText.trim(),url:a?.href};}).filter(x=>x.title)}));
 if(!data.items.length)throw Error('未读取题录，请检查结果页面。');
 return {source:'中文社会科学引文索引 CSSCI',query:q,field:'篇名(词)',page:1,...data,note:'首屏来源文献题录；不访问全文，机构识别不保证全文权限。'};
}
