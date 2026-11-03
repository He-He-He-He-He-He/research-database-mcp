"""最高人民法院司法解释栏目：分页目录与原文。"""
import release_runtime
from legal_adapters import CaseList
from court_judicial_statistics_adapters import _get, court_judicial_statistics_detail

def court_interpretations_list(page=1, keyword=''):
    if isinstance(page, bool) or not (isinstance(page, int) or (isinstance(page, str) and page.isascii() and page.isdigit())):
        raise ValueError('页码须为整数')
    if not isinstance(keyword, str):
        raise ValueError('关键词须为字符串')
    page = int(page)
    if not 1 <= page <= 100:
        raise ValueError('页码应为 1—100')
    url = 'https://www.court.gov.cn/fabu/gengduo/16' + ('' if page == 1 else f'_{page}') + '.html'
    parser = CaseList()
    parser.feed(_get(url))
    if not parser.items:
        raise ValueError('未找到目录；可能超出页数或网站改版')
    rows = []
    for item in parser.items:
        item['title'] = ' '.join(item['title'].split())
        if keyword.casefold() in item['title'].casefold():
            rows.append(item)
    return {'page': page, 'source_url': url, 'scope': '关键词只筛选当前页标题；栏目还包含解读和新闻，效力及后续修订须另行核验。', 'items': rows}

def court_interpretations_detail(page_id):
    result = court_judicial_statistics_detail(page_id)
    result['note'] = '官网原文或发布解读；是否施行、已修订或废止须查最新权威版本。图片和附件仅返回链接。'
    return result

def court_interpretations_search_pages(keyword='', start_page=1, end_page=3):
    if not isinstance(keyword, str):
        raise ValueError('关键词须为字符串')
    if any((not isinstance(x, int) or isinstance(x, bool) for x in (start_page, end_page))) or not 1 <= start_page <= end_page <= 100 or end_page - start_page >= 20:
        raise ValueError('起止页须为 1–100 的整数，最多查询连续 20 页')
    items = []
    sources = []
    seen = set()
    for page in range(start_page, end_page + 1):
        result = court_interpretations_list(page, keyword)
        sources.append(result['source_url'])
        for item in result['items']:
            if item['url'] in seen:
                raise ValueError('跨页出现重复链接，目录可能已更新；请重新查询')
            seen.add(item['url'])
            items.append(item)
    return {'keyword': keyword, 'start_page': start_page, 'end_page': end_page, 'source_urls': sources, 'matched_count': len(items), 'items': items, 'scope': '仅筛选指定页标题，栏目还包含新闻、解读与典型案例，不代表全历史；目录动态变化，跨页并非原子快照。是否施行及后续修订须另核。'}
