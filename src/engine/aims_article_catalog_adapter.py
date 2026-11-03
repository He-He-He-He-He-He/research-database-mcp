"""AIMS Sciences 网站公开文章题录。"""
import release_runtime
import html, re
import requests
URL = 'https://www.aimsciences.org/search-data'
FIELDS = 'titleEn;authors.authorNameEn;keywords.keywordEn;abstractinfoEn;doi'
AGG = 'year;authors.authorNameEn;keywords.keywordEn;classifyinfoEn;journalMeta.titleEn;publishDate'

def search(keyword, page=1, limit=5, field='all'):
    if not isinstance(keyword, str) or not 1 <= len(keyword.strip()) <= 100 or re.search('[\\x00-\\x1f]', keyword):
        raise ValueError('关键词须为 1–100 字单行文本')
    if isinstance(page, bool) or not isinstance(page, int) or (not 1 <= page <= 1000):
        raise ValueError('页码须为 1–1000')
    if isinstance(limit, bool) or not isinstance(limit, int) or (not 1 <= limit <= 10):
        raise ValueError('每页最多返回 10 条')
    fields = {'all': FIELDS, 'title': 'titleEn', 'keywords': 'keywords.keywordEn', 'abstract': 'abstractinfoEn'}
    if field not in fields:
        raise ValueError('不支持的检索字段')
    q = keyword.strip()
    p = {'publisherId': '', 'searchField': fields[field], 'q': q, 'searchType': '0', 'language': 'en', 'pn': page, 'limit': limit, 'filters': '[]', 'sorts': '[]', 'highlightFields': '', 'aggreFields': AGG}
    r = requests.post(URL, params=p, timeout=30)
    r.raise_for_status()
    try:
        d = r.json()
    except ValueError:
        raise RuntimeError('AIMS 未返回 JSON') from None
    if not isinstance(d, dict) or type(d.get('totalCount')) is not int or d['totalCount'] < 0 or (d.get('currentPage') != page) or (not isinstance(d.get('resultlist'), list)) or (len(d['resultlist']) > limit):
        raise RuntimeError('AIMS 搜索响应、总数或页码异常')
    items = []
    for x in d['resultlist']:
        if not isinstance(x, dict) or not isinstance(x.get('id'), str) or (not isinstance(x.get('titleEn'), str)):
            raise RuntimeError('题录缺少编号或标题')
        authors = x.get('authors') or []
        journal = x.get('journalMeta') or {}
        if not isinstance(authors, list) or not isinstance(journal, dict):
            raise RuntimeError('作者或期刊结构异常')
        items.append({'id': x['id'], 'title': html.unescape(re.sub('<[^>]*>', '', x['titleEn'])), 'doi': x.get('doi'), 'authors': [a.get('authorNameEn') for a in authors if isinstance(a, dict)], 'journal': journal.get('titleEn'), 'publish_date_raw': x.get('publishDate'), 'year': x.get('year'), 'volume': x.get('volume'), 'issue': x.get('issue'), 'first_page': x.get('fpage'), 'last_page': x.get('lpage')})
    result = {'source': 'AIMS Sciences 公开文章检索', 'query': q, 'page': page, 'page_size': limit, 'total': d['totalCount'], 'total_pages_raw': d.get('totalPage'), 'items': items[:limit], 'note': '搜索涵盖站方题名、作者、关键词、摘要和 DOI；每页大小由 limit 决定，连续翻页须保持一致。站方全站结果不代表浙大数学学院订购范围，机构身份与逐篇全文权限未验证。'}
    if field != 'all':
        result['field_requested'] = field
        result['note'] = '站方单字段检索，匹配可能分词；摘要字段只用于检索，未返回全文或证明逐篇权限。每页长度由 limit 决定；机构身份未验证，源站超时不代表零结果。'
    return result
