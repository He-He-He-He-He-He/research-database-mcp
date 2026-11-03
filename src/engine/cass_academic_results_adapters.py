"""中国社会科学院学术成果栏目当前目录。"""
import release_runtime
import re
import requests
from urllib.parse import urljoin, urlparse
from szse_chinext_adapters import _Links
from moe_rules_adapters import _Body
BASE = 'https://www.cass.cn/xueshuchengguo/'
PATTERN = re.compile('/xueshuchengguo/[a-z]+/\\d{6}/t\\d{8}_\\d+\\.shtml')

def _get(url):
    p = urlparse(url)
    if p.scheme != 'https' or p.hostname != 'www.cass.cn' or p.query or p.fragment or (not (p.path == '/xueshuchengguo/' or PATTERN.fullmatch(p.path))):
        raise ValueError('仅支持学术成果栏目')
    response = requests.get(url, timeout=20, allow_redirects=False)
    response.raise_for_status()
    if response.status_code != 200:
        raise ValueError('上游返回跳转或非 200')
    response.encoding = 'utf-8'
    return response.text

def cass_academic_results(keyword=''):
    if not isinstance(keyword, str):
        raise ValueError('关键词须为字符串')
    p = _Links()
    p.feed(_get(BASE))
    out = []
    seen = set()
    recognized = False
    for href, title in p.links:
        url = urljoin(BASE, href)
        q = urlparse(url)
        title = ' '.join(title.split())
        if q.hostname == 'www.cass.cn' and (not q.query) and (not q.fragment) and PATTERN.fullmatch(q.path) and title and (title != '【详情】'):
            recognized = True
            if keyword in title and url not in seen:
                seen.add(url)
                out.append({'title': title, 'url': url})
    if not recognized:
        raise ValueError('未识别学术成果目录，无法确认检索结果')
    return out

def cass_academic_result_detail(url):
    p = _Body()
    p.feed(_get(url))
    text = '\n'.join((x.strip() for x in ''.join(p.parts).splitlines() if x.strip()))
    if len(text) < 100:
        raise ValueError('未识别文章正文')
    return {'url': url, 'text': text, 'note': '中国社会科学院学术成果栏目文章；栏目不是全部学术成果或论文全文数据库。'}
