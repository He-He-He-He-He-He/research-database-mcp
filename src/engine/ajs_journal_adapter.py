"""Public American Journal of Science website search metadata."""
import release_runtime
from urllib.parse import urlsplit
import requests
BASE = 'https://ajsonline.org/api/v1/articles.json'

def search(query, page=1, limit=5, session=None):
    if not isinstance(query, str) or not query.strip() or len(query) > 100 or (type(page) is not int) or (page < 1) or (page > 1000) or (type(limit) is not int) or (not 1 <= limit <= 15):
        raise ValueError('关键词、页码或条数无效')
    if session is None:
        session = requests.Session()
        session.trust_env = False
    p = {'journal_id': '2823', 'search': query.strip(), 'offset': (page - 1) * limit, 'per_page': limit, 'sort_column': 'published_at', 'embed': 'section,authors', 'sort_order': 'desc', 'include_unapproved_journals': 'true'}
    r = session.get(BASE, params=p, timeout=20)
    r.raise_for_status()
    if urlsplit(r.url).hostname != 'ajsonline.org':
        raise ValueError('响应跳转至未知域名')
    data = r.json()
    rows = data.get('articles')
    total = data.get('meta', {}).get('total_results')
    if not isinstance(rows, list) or len(rows) > limit or type(total) is not int or any((x.get('journal_id') != 2823 for x in rows)):
        raise ValueError('期刊响应结构或范围不匹配')
    result = []
    for x in rows[:limit]:
        u = urlsplit(x.get('url') or '')
        if u.hostname != 'ajsonline.org' or not u.path.startswith('/article/'):
            raise ValueError('记录链接异常')
        result.append({'id': x.get('id'), 'title': x.get('title'), 'published_at': x.get('published_at'), 'authors': [a.get('name') for a in x.get('authors', []) if a.get('name')], 'type': x.get('formatted_type'), 'url': x.get('url')})
    return {'source': 'American Journal of Science 官网', 'query': query.strip(), 'total': total, 'page': page, 'upstream_page_size': limit, 'items': result, 'note': '官网单刊公开检索题录，按发表时间倒序；翻页时保持 limit 不变，旧版页码位置已改变；馆方旧刊链接已失效，现站历史覆盖、学校订购及全文权限未核实。'}
