"""中国科学院官网科研进展当前目录及正文。"""
import release_runtime
import posixpath
import re
import subprocess
from urllib.parse import urljoin, urlparse
from szse_chinext_adapters import _Links
from women_children_monitor_adapters import _Body
BASE = 'https://www.cas.cn/syky/'
PATTERN = re.compile('/syky/\\d{6}/t\\d{8}_\\d+\\.shtml')

def _get(url):
    p = urlparse(url)
    if p.scheme != 'https' or p.hostname != 'www.cas.cn' or p.query or p.fragment or (not (p.path == '/syky/' or PATTERN.fullmatch(p.path))):
        raise ValueError('仅支持中国科学院科研进展当前目录及文章')
    return release_runtime.run(['curl', '--compressed', '--fail', '--silent', '--show-error', '--max-time', '20', url], check=True, capture_output=True).stdout.decode('utf-8')

def cas_research_progress(keyword=''):
    parser = _Links()
    parser.feed(_get(BASE))
    results = []
    seen = set()
    for href, title in parser.links:
        p = urlparse(urljoin(BASE, href))
        path = posixpath.normpath(p.path)
        if p.hostname == 'www.cas.cn' and (not p.query) and (not p.fragment) and PATTERN.fullmatch(path) and (keyword in title) and (path not in seen):
            seen.add(path)
            results.append({'title': ' '.join(title.split()), 'url': 'https://www.cas.cn' + path})
    if not results and (not keyword):
        raise ValueError('未识别科研进展目录')
    return results

def cas_research_progress_detail(url):
    p = _Body()
    p.feed(_get(url))
    text = '\n'.join((s.strip() for s in ''.join(p.parts).splitlines() if s.strip()))
    if len(text) < 100:
        raise ValueError('未识别正文')
    return {'url': url, 'text': text, 'note': '中国科学院官网科研进展介绍，非论文全文数据库；研究结果及文献请核对原文。'}
