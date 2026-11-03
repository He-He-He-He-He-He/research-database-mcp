/** 术语在线：通过 CUA 读取搜索结果首屏的术语元数据。 */
export async function termonlineSearch(tab, keyword) {
  if (typeof keyword !== 'string' || !keyword.trim() || keyword.length > 100) throw Error('关键词须为 1–100 个字符');
  const query=keyword.trim();
  await tab.goto('https://www.termonline.cn/search?searchText='+encodeURIComponent(query));
  await tab.playwright.getByText('查看详情 >').first().waitFor({state:'visible',timeoutMs:20000});
  const items=await tab.playwright.evaluate(()=>Array.from(document.querySelectorAll('*')).filter(e=>e.children.length===0&&e.innerText?.trim()==='查看详情 >').map(e=>{
    const card=e.parentElement.parentElement.parentElement;
    const header=card.children[0].innerText.split('\n').map(x=>x.trim()).filter(Boolean);
    const lines=card.children[2].innerText.split('\n').map(x=>x.trim()).filter(Boolean);
    const field=(label)=>{const i=lines.indexOf(label);return i<0?'':lines[i+1]||''};
    return {term:header[0],year:header[1]||'',english:field('英文：'),discipline:field('学科：'),source:field('来源：')};
  }));
  return {source:'术语在线',query,page:1,institution:null,items,note:'仅返回当前页术语元数据；未见机构标识；无结果或加载故障可能超时。'};
}
