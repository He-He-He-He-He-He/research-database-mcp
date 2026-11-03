"""教育部 2014—2019 年全国教育统计公开表格目录。"""
import release_runtime
import re
from urllib.parse import urljoin
from moe_education_statistics_adapters import _get, _Links, moe_education_table

def moe_education_legacy_list(year=2019, page=1):
    """返回旧版全国基本情况目录指定页的标题和链接，页码从 1 开始。"""
    year, page = (int(year), int(page))
    if year not in range(2014, 2020) or not 1 <= page <= 100:
        raise ValueError('仅支持 2014—2019 年，页码应为 1—100')
    section = f'{year}_qg' if year <= 2016 else 'qg'
    base = f'https://www.moe.gov.cn/jyb_sjzl/moe_560/jytjsj_{year}/{section}/'
    parser = _Links()
    parser.feed(_get(base if page == 1 else urljoin(base, f'index_{page - 1}.html')))
    items = []
    for href, title in parser.links:
        url = urljoin(base, href)
        if title and re.fullmatch(re.escape(base) + '\\d{6}/t\\d{8}_\\d+\\.html', url):
            items.append({'year': year, 'title': title, 'url': url})
    if not items:
        raise ValueError('未找到表格目录，可能该页不存在或网站改版')
    return items
__all__ = ['moe_education_legacy_list', 'moe_education_table']
