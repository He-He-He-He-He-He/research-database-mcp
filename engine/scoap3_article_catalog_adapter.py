"""SCOAP³ 公开论文题录；站方 search API 而非 records 列表。"""
import release_runtime
import re
import requests
from urllib.parse import urlsplit, parse_qs
URL = 'https://repo.scoap3.org/api/search/article/'

def search(keyword, page=1, limit=5):
    if not isinstance(keyword, str) or not 1 <= len(keyword.strip()) <= 100 or re.search('[\\x00-\\x1f]', keyword):
        raise ValueError('关键词须为 1–100 字单行文本')
    if isinstance(page, bool) or not isinstance(page, int) or (not 1 <= page <= 1000):
        raise ValueError('页码须为 1–1000')
    if isinstance(limit, bool) or not isinstance(limit, int) or (not 1 <= limit <= 10):
        raise ValueError('每页最多返回 10 条')
    q = keyword.strip()
    r = requests.get(URL, params={'search_simple_query_string': q, 'page': page, 'page_size': limit}, timeout=40)
    r.raise_for_status()
    try:
        d = r.json()
    except ValueError:
        raise RuntimeError('SCOAP³ 未返回 JSON') from None
    if not isinstance(d, dict) or type(d.get('count')) is not int or d['count'] < 0 or (not isinstance(d.get('results'), list)) or (len(d['results']) > limit):
        raise RuntimeError('SCOAP³ 题录结构异常')
    next_url = d.get('next')
    if next_url is not None:
        if not isinstance(next_url, str):
            raise RuntimeError('下一页链接异常')
        u = urlsplit(next_url)
        args = parse_qs(u.query)
        if u.scheme != 'https' or u.hostname != 'repo.scoap3.org' or u.path.rstrip('/') != '/api/search/article' or (args.get('page') != [str(page + 1)]) or (args.get('page_size') != [str(limit)]) or (args.get('search_simple_query_string') != [q]):
            raise RuntimeError('原站下一页链接与本次查询不一致')
    items = []
    for x in d['results']:
        if not isinstance(x, dict) or type(x.get('id')) is not int or (not isinstance(x.get('title'), str)):
            raise RuntimeError('题录缺少编号或标题')
        items.append({'id': x['id'], 'title_raw': x['title'], 'doi': x.get('doi'), 'authors_raw': x.get('authors'), 'publication_date': x.get('publication_date'), 'publication_info_raw': x.get('publication_info'), 'abstract_html_raw': x.get('abstract'), 'article_identifiers_raw': x.get('article_identifiers'), 'licenses_raw': x.get('related_licenses')})
    return {'source': 'SCOAP³ Repository 公开论文检索', 'query': q, 'page_requested': page, 'page_size': limit, 'total': d['count'], 'items': items[:limit], 'next_page_available': next_url is not None, 'note': '检索采用原站 simple query 语法，站方分页大小由 limit 决定，连续翻页需保持一致。摘要和标识保留原站原始形式，缺失为 null；按原站许可证字段展示，未逐篇验证全文或许可，学校机构身份与馆方图书子集未核验。'}
