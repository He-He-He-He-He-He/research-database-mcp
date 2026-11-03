"""教育部 2014—2019 年各地教育统计旧版目录。"""
import release_runtime
import re
from urllib.parse import urljoin
from moe_education_statistics_adapters import _get, _Links, moe_education_table

def moe_region_legacy_list(year=2019, page=1):
    """按年份和从 1 起的页码读取各地基本情况目录。"""
    year, page = (int(year), int(page))
    if year not in range(2014, 2020) or not 1 <= page <= 100:
        raise ValueError('仅支持 2014—2019 年，页码应为 1—100')
    section = f'{year}_gd' if year <= 2016 else 'gd'
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
__all__ = ['moe_region_legacy_list', 'moe_education_table']
