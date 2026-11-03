"""Shutongwen Oriental Magazine issue catalog search, not article text."""
import release_runtime
import re
from urllib.parse import quote
import requests
from bs4 import BeautifulSoup
BASE = 'https://gujiku.unihan.com.cn/'

def search(keyword, limit=10, session=None):
    if not isinstance(keyword, str) or not 1 <= len(keyword.strip()) <= 80:
        raise ValueError('关键词须为 1–80 字')
    if not isinstance(limit, int) or isinstance(limit, bool) or (not 1 <= limit <= 30):
        raise ValueError('数量须为 1–30')
    q = keyword.strip()
    s = session or requests.Session()
    r = s.get(BASE + 'Products/Search/QSL', timeout=20)
    r.raise_for_status()
    if not re.search('\\bzjdx\\b', BeautifulSoup(r.content, 'html.parser').get_text(' ', strip=True), re.I):
        raise RuntimeError('未识别学校账户标记')
    r = s.get(BASE + 'minguofy/api/oldcatalog/search/MinGuoFY/' + quote(q, safe=''), timeout=20)
    r.raise_for_status()
    j = r.json()
    ids = j.get('ids') if isinstance(j, dict) else None
    if not isinstance(ids, list) or any((not isinstance(x, str) or not re.fullmatch('c\\d+', x) for x in ids)) or len(set(ids)) != len(ids):
        raise RuntimeError('期次命中编号异常')
    r = s.get(BASE + 'minguofy/api/catalog/get/MinGuoFY', params={'id': 'root'}, timeout=20)
    r.raise_for_status()
    root = r.json()
    if not isinstance(root, list):
        raise RuntimeError('期次总目异常')
    lookup = {x['id']: x['text'] for x in root if isinstance(x, dict) and isinstance(x.get('id'), str) and isinstance(x.get('text'), str)}
    if any((i not in lookup for i in ids)):
        raise RuntimeError('命中期次与原站总目不一致')
    return {'source': '书同文东方杂志总目', 'account_marker': 'zjdx', 'query': q, 'matched_issues': len(ids), 'items': [{'id': i, 'issue': lookup[i]} for i in ids[:limit]], 'note': '返回关键词命中的期次，不是文章标题或全文；原站关联异体字，期次顺序沿用接口返回。'}
