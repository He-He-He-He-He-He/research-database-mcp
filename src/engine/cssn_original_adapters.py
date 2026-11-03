"""中国社会科学网原创资讯当前目录及正文。"""
import release_runtime
import re
import subprocess
from urllib.parse import urljoin, urlparse
from szse_chinext_adapters import _Links
from moe_rules_adapters import _Body
BASE = 'https://www.cssn.cn/skgz/bwyc/'
PATTERN = re.compile('/skgz/bwyc/\\d{6}/t\\d{8}_\\d+\\.shtml')

def _get(url):
    p = urlparse(url)
    if p.scheme != 'https' or p.hostname != 'www.cssn.cn' or p.query or p.fragment or (not (p.path == '/skgz/bwyc/' or PATTERN.fullmatch(p.path))):
        raise ValueError('仅支持中国社会科学网本网站原创当前目录及文章')
    return release_runtime.run(['curl', '--compressed', '--fail', '--silent', '--show-error', '--max-time', '20', url], check=True, capture_output=True).stdout.decode('utf-8')

def cssn_original_articles(keyword=''):
    parser = _Links()
    parser.feed(_get(BASE))
    results = []
    seen = set()
    for href, title in parser.links:
        url = urljoin(BASE, href)
        p = urlparse(url)
        if p.hostname == 'www.cssn.cn' and (not p.query) and (not p.fragment) and PATTERN.fullmatch(p.path) and (keyword in title) and (url not in seen):
            seen.add(url)
            results.append({'title': ' '.join(title.split()), 'url': url})
    if not results and (not keyword):
        raise ValueError('未识别原创资讯目录')
    return results

def cssn_original_article_detail(url):
    p = _Body()
    p.feed(_get(url))
    text = '\n'.join((s.strip() for s in ''.join(p.parts).splitlines() if s.strip()))
    if len(text) < 100:
        raise ValueError('未识别正文')
    return {'url': url, 'text': text, 'note': '中国社会科学网本网站原创资讯，非论文全文或全部社科成果；来源及研究内容应核对原始资料。'}
