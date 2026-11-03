"""中国生物物种名录公开网页名称检索及物种详情。站点仅 HTTP。"""
import release_runtime
import re
from urllib.parse import urljoin, urlsplit
import requests
from bs4 import BeautifulSoup
BASE = 'http://www.sp2000.org.cn/'

def _valid(r):
    r.raise_for_status()
    if r.is_redirect or len(r.content) > 6000000:
        raise ValueError('上游返回跳转或过大')
    return r

def search(keyword, page=1, limit=10):
    if not isinstance(keyword, str) or not keyword.strip() or len(keyword) > 100:
        raise ValueError('输入1–100字符物种名称')
    if any((isinstance(x, bool) or not isinstance(x, int) for x in (page, limit))) or not 1 <= page <= 100 or (not 1 <= limit <= 100):
        raise ValueError('页码及数量须在1–100')
    s = requests.Session()
    r = _valid(s.get(BASE + 'search/search_all_names', timeout=20, allow_redirects=False))
    form = BeautifulSoup(r.content, 'html.parser')
    token = form.select_one('input[name="_csrf"]')
    if not token or not token.get('value'):
        raise ValueError('未获取网站表单令牌')
    r = _valid(s.post(BASE + 'search/search_all_names_results', data={'search_text': keyword.strip(), 'match_option': 'fuzzy', '_csrf': token['value']}, timeout=25, allow_redirects=False))
    result = BeautifulSoup(r.content, 'html.parser')
    tab = result.select_one('#results_table[data-url]')
    if not tab:
        raise ValueError('未识别结果表；无匹配或网站结构变化')
    u = urljoin(BASE, tab['data-url'])
    p = urlsplit(u)
    if p.scheme != 'http' or p.hostname != 'www.sp2000.org.cn' or p.path != '/rest/search/search_all_names_results_table':
        raise ValueError('网站返回异常结果链接')
    d = _valid(s.get(u, params={'limit': limit, 'offset': (page - 1) * limit}, timeout=25, allow_redirects=False)).json()
    if not isinstance(d.get('rows'), list) or not isinstance(d.get('total'), int):
        raise ValueError('结果格式变化')
    rows = []
    for row in d['rows']:
        link = BeautifulSoup(str(row.get('show_details') or ''), 'html.parser').find('a', href=True)
        detail = urljoin(BASE, link['href']) if link else None
        dp = urlsplit(detail or '')
        if detail and (dp.scheme != 'http' or dp.hostname != 'www.sp2000.org.cn' or (not re.fullmatch('/(?:species/show_species_details/[a-f0-9]{32}|browse/browse_this_taxa/[a-f0-9-]+)', dp.path))):
            detail = None
        rows.append({'name': BeautifulSoup(str(row.get('name') or ''), 'html.parser').get_text(' ', strip=True), 'chinese_name': row.get('name_c'), 'rank': row.get('rank'), 'name_status': row.get('name_status'), 'source_database': row.get('source_database'), 'detail_url': detail})
    return {'source': '中国生物物种名录', 'source_url': BASE, 'keyword': keyword, 'page': page, 'page_size': limit, 'total': d['total'], 'items': rows, 'note': '站点目前使用未加密 HTTP，关键词和结果可能被网络中间方读取或篡改；不输入敏感信息。搜索返回名称及分类记录，不等同保护等级或完整分布。'}

def detail(species_id):
    if not isinstance(species_id, str) or not re.fullmatch('[a-f0-9]{32}', species_id):
        raise ValueError('物种 ID 须为32位小写十六进制')
    url = BASE + 'species/show_species_details/' + species_id
    r = _valid(requests.get(url, timeout=25, allow_redirects=False))
    s = BeautifulSoup(r.content, 'html.parser')
    fields = []
    for tr in s.select('tr'):
        label = tr.select_one('td.details_title')
        cells = tr.find_all('td', recursive=False)
        if label and len(cells) >= 2:
            fields.append({'label': label.get_text(' ', strip=True), 'value': cells[1].get_text(' ', strip=True)})
    if not fields or not any(('接受的学名' in f['label'] for f in fields)):
        raise ValueError('未识别物种详情')
    return {'source': '中国生物物种名录', 'source_url': url, 'fields': fields, 'note': '目前采用未加密 HTTP，结果可能被篡改；分布可能不完整，保护身份需另查最新官方名录。'}
