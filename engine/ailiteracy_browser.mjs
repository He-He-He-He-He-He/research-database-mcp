/** AI素养与技能提升数据库课程单页搜索，使用 CUA Tab。 */
export async function aiLiteracySearch(tab, keyword) {
 if(typeof keyword!=='string'||!keyword.trim()||keyword.trim().length>100) throw Error('关键词须为 1–100 个字符');
 const query=keyword.trim(); await tab.goto('https://ai.xxsuyang.com/search?keyword='+encodeURIComponent(query));
 await tab.playwright.locator('.course-box .ctitle').first().waitFor({state:'visible',timeoutMs:20000});
 const data=await tab.playwright.evaluate(()=>({institution:document.body.innerText.includes('浙江大学 欢迎您')?'浙江大学':null,items:Array.from(document.querySelectorAll('.course-box')).map(e=>({title:e.querySelector('.ctitle')?.innerText.trim()||'',views:e.querySelector('.cplc')?.innerText.trim()||''})).filter(x=>x.title)}));
 return {source:'AI素养与技能提升数据库',query,page:1,...data,note:'当前页课程题录；机构标识异步加载，未显示时为 null，视频播放权限未验证。无结果或页面变化可能超时。'};
}
