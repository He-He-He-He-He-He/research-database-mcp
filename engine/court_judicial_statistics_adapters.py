"""最高人民法院司法数据栏目：分页目录与原文、附件链接。"""
import release_runtime
import re
import subprocess
from urllib.parse import urljoin, urlparse
from legal_adapters import CaseList, CaseDetail
BASE = 'https://www.court.gov.cn'

def _get(url):
    p = urlparse(url)
    if p.scheme != 'https' or p.hostname != 'www.court.gov.cn':
        raise ValueError('仅允许最高人民法院官网 HTTPS 链接')
    return release_runtime.run(['curl', '--fail', '--silent', '--show-error', '--max-time', '20', url], check=True, capture_output=True).stdout.decode('utf-8')

class _Detail(CaseDetail):

    def __init__(self):
        super().__init__()
        self.resources = []

    def handle_starttag(self, tag, attrs):
        if self.depth:
            attrs_dict = dict(attrs)
            href = attrs_dict.get('href') if tag == 'a' else attrs_dict.get('src') if tag == 'img' else None
            if href:
                url = urljoin(BASE, href)
                p = urlparse(url)
                if p.scheme == 'https' and p.hostname == 'www.court.gov.cn':
                    self.resources.append({'kind': 'image' if tag == 'img' else 'link', 'url': url})
        super().handle_starttag(tag, attrs)

def court_judicial_statistics_list(page=1, keyword=''):
    if isinstance(page, bool) or not (isinstance(page, int) or (isinstance(page, str) and page.isascii() and page.isdigit())):
        raise ValueError('页码须为整数')
    if not isinstance(keyword, str):
        raise ValueError('关键词须为字符串')
    page = int(page)
    if not 1 <= page <= 100:
        raise ValueError('页码应为 1—100')
    url = f'{BASE}/fabu/gengduo/21' + ('' if page == 1 else f'_{page}') + '.html'
    parser = CaseList()
    parser.feed(_get(url))
    if not parser.items:
        raise ValueError('未找到目录；可能超出页数或网站改版')
    return {'page': page, 'source_url': url, 'scope': '关键词只过滤本页标题', 'items': [item for item in parser.items if keyword.casefold() in item['title'].casefold()]}

def court_judicial_statistics_search_pages(keyword='', start_page=1, end_page=3):
    """只筛选指定连续页面，不代表全部历史或完整数据库。"""
    if not isinstance(keyword, str):
        raise ValueError('关键词须为字符串')
    if any((not isinstance(x, int) or isinstance(x, bool) for x in (start_page, end_page))) or not 1 <= start_page <= end_page <= 100 or end_page - start_page >= 20:
        raise ValueError('起止页须为 1–100 的整数，最多查询连续 20 页')
    items = []
    sources = []
    seen = set()
    for page in range(start_page, end_page + 1):
        result = court_judicial_statistics_list(page, keyword)
        sources.append(result['source_url'])
        for item in result['items']:
            if item['url'] in seen:
                raise ValueError('跨页出现重复链接，目录可能已更新；请重新查询')
            seen.add(item['url'])
            items.append(item)
    return {'keyword': keyword, 'start_page': start_page, 'end_page': end_page, 'source_urls': sources, 'matched_count': len(items), 'items': items, 'scope': '仅筛选指定页标题，栏目包括其他司法数据；目录动态更新，跨页并非原子快照，不代表全部历史或所有司法统计。标题相同不代表同一文献。'}

def court_judicial_statistics_detail(page_id):
    if not re.fullmatch('\\d{1,12}', str(page_id)):
        raise ValueError('页面 ID 须为数字')
    url = f'{BASE}/fabu/xiangqing/{page_id}.html'
    parser = _Detail()
    parser.feed(_get(url))
    if not parser.found:
        raise ValueError('未发现正文；网站可能改版')
    return {'source_url': url, 'text': ''.join(parser.text).strip(), 'resources': parser.resources, 'note': '正文可能仅含下载链接或图表；单位、时段及统计口径以原文和附件为准。'}
