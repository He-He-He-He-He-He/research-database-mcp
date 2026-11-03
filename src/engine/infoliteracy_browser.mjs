/* 高校信息素养教育数据库：课程题目检索单页，不播放。 */
export async function infoLiteracySearch(tab,keyword){
 if(typeof keyword!=='string'||!keyword.trim()||keyword.length>100)throw Error('关键词需为 1–100 字');
 const u=new URL('https://suyang.zxhnzq.com/search');u.search=new URLSearchParams({keyword:keyword.trim()}).toString();await tab.goto(u.toString());
 try{await tab.playwright.locator('.course-box .course-name').first().waitFor({state:'visible',timeoutMs:15000});}catch(_){throw Error('未读取课程，可能无结果、登录或页面变化。');}
 const data=await tab.playwright.evaluate(()=>({institution:document.body.innerText.includes('浙江大学 欢迎您')?'浙江大学':null,items:[...document.querySelectorAll('.course-box')].map(e=>({title:e.querySelector('.course-name')?.innerText.trim(),description:e.querySelector('.course-desc')?.innerText.trim(),learners:e.querySelector('.course-btm-left')?.innerText.trim()})).filter(x=>x.title)}));
 return {source:'高校信息素养教育数据库',query:keyword.trim(),page:1,...data,note:'首屏课程目录，不代表课程播放权限。'};
}
