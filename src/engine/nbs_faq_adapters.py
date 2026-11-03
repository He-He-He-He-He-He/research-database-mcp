"""国家统计局常见问题解答当前目录与正文。"""
import release_runtime
import re
import requests
from urllib.parse import urljoin, urlparse
from szse_chinext_adapters import _Links
from women_children_monitor_adapters import _Body
BASE = 'https://www.stats.gov.cn/hd/cjwtjd/'
PATTERN = re.compile('/hd/cjwtjd/\\d{6}/t\\d{8}_\\d+\\.html')

def _get(url):
    p = urlparse(url)
    if p.scheme != 'https' or p.hostname != 'www.stats.gov.cn' or p.query or p.fragment or (not (p.path == '/hd/cjwtjd/' or PATTERN.fullmatch(p.path))):
        raise ValueError('仅支持国家统计局常见问题栏目')
    r = requests.get(url, timeout=20, allow_redirects=False)
    if r.status_code != 200:
        raise RuntimeError('上游 HTTP ' + str(r.status_code))
    r.encoding = 'utf-8'
    return r.text

def nbs_faq_topics(keyword=''):
    p = _Links()
    p.feed(_get(BASE))
    out = []
    seen = set()
    for href, title in p.links:
        url = urljoin(BASE, href)
        q = urlparse(url)
        title = ' '.join(title.split())
        if q.hostname == 'www.stats.gov.cn' and (not q.query) and (not q.fragment) and PATTERN.fullmatch(q.path) and (keyword in title) and (url not in seen):
            seen.add(url)
            out.append({'title': title, 'url': url})
    if not out and (not keyword):
        raise ValueError('未识别常见问题目录')
    return out

def nbs_faq_detail(url):
    p = _Body()
    p.feed(_get(url))
    text = '\n'.join((x.strip() for x in ''.join(p.parts).splitlines() if x.strip()))
    if len(text) < 100:
        raise ValueError('未识别常见问题正文')
    return {'url': url, 'text': text, 'note': '统计局常见问题专题，内容反映发布时制度与口径，应核对最新官方资料。'}
