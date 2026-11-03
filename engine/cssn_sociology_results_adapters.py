"""中国社会科学网社会学学术成果栏目当前页。"""
import release_runtime
import re
import subprocess
from urllib.parse import urljoin, urlparse
from szse_chinext_adapters import _Links
from moe_rules_adapters import _Body
BASE = 'https://www.cssn.cn/shx/shx_xscg/'
PATTERN = re.compile('/shx/shx_xscg/\\d{6}/t\\d{8}_\\d+\\.shtml')

def _get(url):
    p = urlparse(url)
    if p.scheme != 'https' or p.hostname != 'www.cssn.cn' or p.query or p.fragment or (not (p.path == '/shx/shx_xscg/' or PATTERN.fullmatch(p.path))):
        raise ValueError('仅支持社会学学术成果栏目')
    return release_runtime.run(['curl', '--compressed', '--fail', '--silent', '--show-error', '--max-time', '20', url], check=True, capture_output=True).stdout.decode('utf-8')

def cssn_sociology_results(keyword=''):
    p = _Links()
    p.feed(_get(BASE))
    out = []
    seen = set()
    for href, title in p.links:
        url = urljoin(BASE, href)
        q = urlparse(url)
        title = ' '.join(title.split())
        if q.hostname == 'www.cssn.cn' and (not q.query) and (not q.fragment) and PATTERN.fullmatch(q.path) and (keyword in title) and (url not in seen):
            seen.add(url)
            out.append({'title': title, 'url': url})
    if not out and (not keyword):
        raise ValueError('未识别社会学成果目录')
    return out

def cssn_sociology_result_detail(url):
    p = _Body()
    p.feed(_get(url))
    text = '\n'.join((x.strip() for x in ''.join(p.parts).splitlines() if x.strip()))
    if len(text) < 100:
        raise ValueError('正文可能是图片或网页结构变化')
    return {'url': url, 'text': text, 'note': '中国社会科学网社会学成果栏目文章，非完整论文数据库，观点和来源应核对原页。'}
