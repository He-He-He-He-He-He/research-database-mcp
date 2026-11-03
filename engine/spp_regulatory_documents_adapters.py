"""最高检规范文件栏目。"""
import release_runtime
from spp_interpretations_adapters import _List, spp_interpretations_detail
from spp_typical_cases_adapters import _get
BASE = 'https://www.spp.gov.cn/spp/flfg/gfwj/'

def spp_regulatory_documents_list(page=1, keyword=''):
    page = int(page)
    if not 1 <= page <= 100:
        raise ValueError('页码应为 1—100')
    url = BASE + ('index.shtml' if page == 1 else f'index_{page}.shtml')
    parser = _List(BASE)
    parser.feed(_get(url))
    if not parser.rows:
        raise ValueError('未找到目录；页码可能超出范围或网站改版')
    return {'page': page, 'source_url': url, 'scope': '关键词仅筛选本页标题；具体效力和修订须核查。', 'items': [row for row in parser.rows if keyword.casefold() in row['title'].casefold()]}

def spp_regulatory_documents_detail(url):
    result = spp_interpretations_detail(url)
    result['note'] = '返回完整文章而非锚点片段；可能为发布会合集或解读，具体效力和后续修订须核查。'
    return result
