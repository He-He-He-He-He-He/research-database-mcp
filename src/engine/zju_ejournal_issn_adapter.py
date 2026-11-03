"""浙江大学电子书刊导航的 ISSN/ISBN 精确检索与站方覆盖期。"""
import release_runtime
import re
from urllib.parse import urljoin, parse_qs, urlsplit
import requests
from bs4 import BeautifulSoup
BASE = 'https://gk4pb6yy8y.search.serialssolutions.com/'

def search(identifier):
    if not isinstance(identifier, str) or not re.fullmatch('[0-9Xx-]{8,20}', identifier.strip()):
        raise ValueError('请输入有效格式的 ISSN 或 ISBN')
    return _search(identifier.strip(), 'I_M', 'ISSN/ISBN 等于', 100)

def title_search(title, mode='exact', limit=10, page=1):
    if not isinstance(title, str) or not 1 <= len(title.strip()) <= 100 or any((ord(c) < 32 for c in title)):
        raise ValueError('书刊标题须为 1–100 字单行文本')
    if mode not in ('exact', 'all'):
        raise ValueError('匹配方式须为 exact 或 all')
    if type(limit) is not int or not 1 <= limit <= 200:
        raise ValueError('返回条数须为 1–200')
    if type(page) is not int or not 1 <= page <= 1000:
        raise ValueError('源站页码须为 1–1000')
    return _search(title.strip(), 'A_T_M' if mode == 'exact' else 'T_W_A', '标题等于' if mode == 'exact' else '标题包含所有词', limit, page)

def _search(q, mode, mode_label, limit, page=1):
    params = {'V': '1.0', 'N': '100', 'tab': 'ALL', 'L': 'GK4PB6YY8Y', 'S': mode, 'C': q}
    if page > 1:
        params['B'] = str((page - 1) * 100)
    r = requests.get(BASE, params=params, timeout=30)
    r.raise_for_status()
    p = BeautifulSoup(r.content, 'html.parser')
    count = p.select_one('.SS_ResultsCount')
    m = re.search('([\\d,]+)\\s*记录', count.get_text(' ', strip=True) if count else '')
    if not m:
        raise RuntimeError('未识别浙大电子书刊导航结果总数')
    total = int(m.group(1).replace(',', ''))
    items = []
    text = p.get_text(' ', strip=True)
    rng = re.search('当前记录[：:]\\s*([\\d,]+)\\s*-\\s*([\\d,]+)', text)
    if page > 1 and total and (not rng or int(rng.group(1).replace(',', '')) != (page - 1) * 100 + 1):
        raise RuntimeError('源站未确认所请求的记录范围')
    for box in p.select('.SS_Holding'):
        title = box.select_one('.SS_JournalTitle')
        issn = box.select_one('.SS_JournalISSN')
        if not title or not title.get_text(' ', strip=True):
            continue
        holdings = []
        for td in box.select('td.SS_HoldingData'):
            date = td.select_one('.SS_JournalCoverageDates')
            providers = []
            for a in td.select('a.SS_JournalHyperLink'):
                h = a.get('href', '')
                target = parse_qs(urlsplit(urljoin(BASE, h)).query).get('U', [None])[0]
                if target and urlsplit(target).scheme not in ('http', 'https'):
                    target = None
                providers.append({'name': a.get_text(' ', strip=True), 'url': target})
            holdings.append({'coverage_raw': date.get_text(' ', strip=True) if date else None, 'providers': providers})
        items.append({'title': title.get_text(' ', strip=True), 'identifier_display': issn.get_text(' ', strip=True) if issn else None, 'holdings': holdings})
    if total and (not items):
        raise RuntimeError('存在结果但未识别任何馆藏条目')
    return {'source': '浙江大学图书馆电子书刊导航', 'query': q, 'mode': mode_label, 'source_total': total, 'source_page': page, 'source_records_range_raw': [int(rng.group(1).replace(',', '')), int(rng.group(2).replace(',', ''))] if rng else None, 'source_items_count': len(items), 'truncated': len(items) > limit, 'items': items[:limit], 'note': '按原站每页 100 条记录分页，当前页书刊条目数可能与记录数不同；如 truncated 为真，可增大 limit 后重查本页；若达到上限仍截断，当前页尚不支持完整读取。站方平台与覆盖区间原样保留；标题匹配可能包含相关题名，覆盖与实际权限可能变化，不能保证全文可用。'}
