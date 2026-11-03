"""国家统计局统计知识库公开检索与知识正文。"""
import release_runtime
import re
import requests
from html.parser import HTMLParser
from urllib.parse import urlparse
from women_children_monitor_adapters import _Body
SEARCH = 'https://api.so-gov.cn/query/s'
PATH = re.compile('/zs/[a-z0-9_/]+/\\d{6}/t\\d{8}_\\d+\\.html')

class _Text(HTMLParser):

    def __init__(self):
        super().__init__()
        self.parts = []

    def handle_data(self, s):
        self.parts.append(s)

def _plain(s):
    p = _Text()
    p.feed(s or '')
    return ' '.join(''.join(p.parts).split())

def nbs_knowledge_search(keyword, page=1, size=10):
    if not isinstance(keyword, str) or not keyword.strip() or len(keyword) > 100 or (not isinstance(page, int)) or (not 1 <= page <= 100) or (not isinstance(size, int)) or (not 1 <= size <= 50):
        raise ValueError('请检查关键词及分页')
    p = {'siteCode': 'bm36000002_zsk', 'tab': 'c29b41e92ababbaf6c6fd870431fee34', 'page': page, 'pageSize': size, 'qt': keyword}
    r = requests.post(SEARCH, data=p, timeout=20, allow_redirects=False)
    if r.status_code != 200:
        raise RuntimeError('上游 HTTP ' + str(r.status_code))
    x = r.json()
    if not x.get('ok'):
        raise ValueError('上游未返回知识检索结果')
    data = x['data']['result']['search']
    out = []
    for d in data.get('docs', []):
        u = d.get('url', '')
        q = urlparse(u)
        if q.scheme == 'https' and q.hostname == 'www.stats.gov.cn' and (not q.query) and (not q.fragment) and PATH.fullmatch(q.path):
            out.append({'title': _plain(d.get('titleO') or d.get('title')), 'url': u, 'summary': _plain(d.get('summary'))})
    return {'total': data.get('total'), 'page': page, 'items': out, 'note': '统计知识库检索；仅保留统计局知识栏目可读取的网页链接。'}

def nbs_knowledge_detail(url):
    p = urlparse(url)
    if p.scheme != 'https' or p.hostname != 'www.stats.gov.cn' or p.query or p.fragment or (not PATH.fullmatch(p.path)):
        raise ValueError('仅支持统计局知识栏目正文')
    r = requests.get(url, timeout=20, allow_redirects=False)
    if r.status_code != 200:
        raise RuntimeError('上游 HTTP ' + str(r.status_code))
    r.encoding = 'utf-8'
    b = _Body()
    b.feed(r.text)
    text = '\n'.join((s.strip() for s in ''.join(b.parts).splitlines() if s.strip()))
    if len(text) < 100:
        raise ValueError('未识别正文')
    return {'url': url, 'text': text, 'note': '知识解释以原文发布时的统计口径为准，应核对最新制度。'}
