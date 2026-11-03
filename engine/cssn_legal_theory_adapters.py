"""中国社会科学网法学理论栏目当前页。"""
import release_runtime
import re
import subprocess
from urllib.parse import urljoin, urlparse
from szse_chinext_adapters import _Links
from moe_rules_adapters import _Body
BASE = 'https://www.cssn.cn/fx/flx/'
PATTERN = re.compile('/fx/flx/\\d{6}/t\\d{8}_\\d+\\.shtml')

def _get(url):
    p = urlparse(url)
    if p.scheme != 'https' or p.hostname != 'www.cssn.cn' or p.query or p.fragment or (not (p.path == '/fx/flx/' or PATTERN.fullmatch(p.path))):
        raise ValueError('仅支持法学理论栏目当前页与正文')
    return release_runtime.run(['curl', '--compressed', '--fail', '--silent', '--show-error', '--max-time', '20', url], check=True, capture_output=True).stdout.decode('utf-8')

def cssn_legal_theory(keyword=''):
    if not isinstance(keyword, str):
        raise ValueError('关键词须为字符串')
    parser = _Links()
    parser.feed(_get(BASE))
    results = []
    seen = set()
    recognized = False
    for href, title in parser.links:
        url = urljoin(BASE, href)
        p = urlparse(url)
        if p.hostname == 'www.cssn.cn' and (not p.query) and (not p.fragment) and PATTERN.fullmatch(p.path) and title.strip():
            recognized = True
            if keyword in title and url not in seen:
                seen.add(url)
                results.append({'title': ' '.join(title.split()), 'url': url})
    if not recognized:
        raise ValueError('未识别法学理论栏目，无法确认检索结果')
    return results

class _Article(_Body):

    def __init__(self):
        super().__init__()
        self.images = []

    def handle_starttag(self, tag, attrs):
        super().handle_starttag(tag, attrs)
        if self.depth and tag == 'img':
            self.images.append(dict(attrs).get('src', ''))

def cssn_legal_theory_detail(url):
    p = _Article()
    p.feed(_get(url))
    text = '\n'.join((s.strip() for s in ''.join(p.parts).splitlines() if s.strip()))
    images = [urljoin(url, x) for x in p.images if x and urlparse(urljoin(url, x)).hostname == 'www.cssn.cn']
    if len(text) < 100 and (not images):
        raise ValueError('未识别正文')
    return {'url': url, 'text': text, 'images': images, 'note': '中国社会科学网法学理论栏目文章；部分正文为图片，未进行 OCR。具体来源、发表信息及作者观点以原页为准，不是裁判文书。'}
