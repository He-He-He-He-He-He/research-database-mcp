/** 尚唯 GPD 产品选型单页题录，使用已绑定 CUA 工作 Tab。 */
export async function gpdSearch(tab, keyword) {
 if(typeof keyword!=='string'||!keyword.trim()||keyword.trim().length>100) throw Error('关键词须为 1–100 个字符');
 const query=keyword.trim(); await tab.goto('https://gpd.sunwayinfo.com.cn/');
 await tab.playwright.getByPlaceholder('请输入搜索关键词',{exact:true}).fill(query);
 await tab.playwright.getByRole('button',{name:'立即搜索',exact:true}).click();
 await tab.playwright.locator('.table_item_right .title span').first().waitFor({state:'visible',timeoutMs:20000});
 const data=await tab.playwright.evaluate(()=>({institution:document.body.innerText.includes('浙江大学')?'浙江大学':null,items:Array.from(document.querySelectorAll('.table_item_right .title span')).map(e=>({title:e.innerText.trim()})).filter(x=>x.title)}));
 return {source:'尚唯产品样本数据库',query,page:1,...data,note:'默认产品选型当前页；未验证详情与下载，无结果或页面变化可能超时。'};
}
