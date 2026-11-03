"""最高人民检察院指导性案例批次目录与正文。"""
import release_runtime
import re
from urllib.parse import urljoin, urlparse
from szse_chinext_adapters import _Links
from spp_typical_cases_adapters import _Body, _get, _CasePage
BASE = 'https://www.spp.gov.cn/spp/jczdal/'
DIRECT_PATH = '/spp/jczdal/\\d{6}/t\\d{8}_\\d+\\.shtml'
RELEASE_PATH = '/(?:spp/)?xwfbh/(?:wsfbh|wsfbt)/\\d{6}/t\\d{8}_\\d+\\.shtml'

def spp_guiding_list(keyword=''):
    if not isinstance(keyword, str):
        raise ValueError('关键词须为字符串')
    p = _Links()
    p.feed(_get(BASE))
    out = []
    recognized = False
    for href, title in p.links:
        x = urlparse(urljoin(BASE, href))
        if x.hostname == 'www.spp.gov.cn' and re.fullmatch('/spp/jczdal/\\d{6}/t\\d{8}_\\d+\\.shtml', x.path):
            recognized = True
            if keyword in title:
                out.append({'title': title, 'url': 'https://www.spp.gov.cn' + x.path})
    if not recognized:
        raise ValueError('未识别指导性案例目录，无法确认检索结果')
    return out

def spp_guiding_search_all(keyword='', limit=30, offset=0):
    if not isinstance(keyword, str):
        raise ValueError('关键词须为字符串')
    if any((not isinstance(x, int) or isinstance(x, bool) for x in (limit, offset))) or not 1 <= limit <= 100 or (not 0 <= offset <= 100000):
        raise ValueError('limit 须为 1–100，offset 须为 0–100000')

    def page(n):
        source = BASE + ('index.shtml' if n == 1 else f'index_{n}.shtml')
        html = _get(source)
        m = re.search('createPageHTML\\(\\s*[\'\\"]page_div[\'\\"]\\s*,\\s*(\\d+)\\s*,\\s*(\\d+)\\s*,\\s*[\'\\"]index[\'\\"]\\s*,\\s*[\'\\"]shtml[\'\\"]\\s*,\\s*(\\d+)\\s*\\)', html)
        if not m or int(m.group(2)) != n:
            raise ValueError('来源页码或分页信息无法核验')
        p = _CasePage()
        p.feed(html)
        if not p.rows:
            raise ValueError('未识别案例批次目录')
        return (int(m.group(1)), int(m.group(3)), p.rows)
    pages, total, first = page(1)
    if not 1 <= pages <= 20 or not 0 <= total <= 2000:
        raise ValueError('目录超过本次遍历上限')
    rows = []
    seen = set()
    for n in range(1, pages + 1):
        p, t, items = (pages, total, first) if n == 1 else page(n)
        if (p, t) != (pages, total):
            raise ValueError('来源目录分页或总数变化')
        for item in items:
            u = urlparse(urljoin(BASE, item['source_href']))
            if not item['title'] or u.scheme != 'https' or u.netloc != 'www.spp.gov.cn' or u.query or (not re.fullmatch('/(?:[\\w-]+/)*t\\d{8}_\\d+\\.shtml', u.path)):
                raise ValueError('来源标题或官方链接无法识别')
            url = 'https://www.spp.gov.cn' + u.path + ('#' + u.fragment if u.fragment else '')
            if url in seen:
                raise ValueError('跨页出现重复来源链接')
            supported = bool(not u.fragment and re.fullmatch(DIRECT_PATH, u.path) or (re.fullmatch(RELEASE_PATH, u.path) and (not u.fragment or u.fragment.isdigit())))
            seen.add(url)
            rows.append({'title': item['title'], 'date': item['date'], 'url': url, 'detail_supported': supported})
    if len(rows) != total:
        raise ValueError('来源目录总数与解析条目不一致')
    matches = [row for row in rows if keyword in row['title']]
    selected = matches[offset:offset + limit]
    return {'source': '最高人民检察院指导性案例批次目录', 'keyword': keyword, 'source_pages': pages, 'source_total': total, 'matched_count': len(matches), 'offset': offset, 'limit': limit, 'next_offset': offset + len(selected) if offset + len(selected) < len(matches) else None, 'items': selected, 'note': '逐页读取当前目录并筛选批次标题；目录动态更新，跨页非原子快照，偏移可能变化。保留来源锚点；详情接口对部分官方发布会链接返回完整文章而非锚点对应片段。每项为案例批次，不是单案数量；参照适用状态须核最新规定。'}

def spp_guiding_detail(url):
    x = urlparse(url)
    if x.scheme != 'https' or x.netloc != 'www.spp.gov.cn' or x.query:
        raise ValueError('仅支持最高检官网 HTTPS 案例文章')
    if re.fullmatch(RELEASE_PATH, x.path) and (not x.fragment or x.fragment.isdigit()):
        from spp_interpretations_adapters import spp_interpretations_detail
        result = spp_interpretations_detail(url)
        return {'url': url, 'text': result['text'], 'anchor': result['anchor'], 'note': '最高检官方发布会完整文章，保留来源锚点但未自动截取锚点对应片段；批次参照适用状态请核对最新规定。'}
    if x.fragment or not re.fullmatch(DIRECT_PATH, x.path):
        raise ValueError('仅支持最高检指导性案例目录内文章或官方发布会链接')
    p = _Body()
    p.feed(_get(url))
    text = '\n'.join((s.strip() for s in ''.join(p.parts).splitlines() if s.strip()))
    if len(text) < 100:
        raise ValueError('未识别案例正文')
    return {'url': url, 'text': text, 'note': '最高检指导性案例批次正文，不是裁判文书全文集；参照适用状态请核对最新规定。'}
