"""国家自然科学基金委 2024 年度报告资助统计章节图片目录。"""
import release_runtime
import re
import subprocess
from html.parser import HTMLParser
from urllib.parse import urljoin, urlparse
from szse_chinext_adapters import _Links
BASE = 'https://www.nsfc.gov.cn'
INDEX = BASE + '/p1/2991/3821/3824/zzqkyzzxm.html'

def _get(url):
    p = urlparse(url)
    if p.scheme != 'https' or p.hostname != 'www.nsfc.gov.cn' or (not p.path.startswith('/p1/2991/3821/3824/')) or p.query or p.fragment:
        raise ValueError('仅允许基金委 2024 年度报告资助章节')
    return release_runtime.run(['curl', '--compressed', '--fail', '--silent', '--show-error', '--max-time', '20', url], check=True, capture_output=True).stdout.decode('utf-8')

def nsfc_annual_sections(keyword=''):
    p = _Links()
    p.feed(_get(INDEX))
    out = []
    seen = set()
    for href, title in p.links:
        if re.fullmatch('/p1/2991/3821/3824/3830/\\d+\\.html', href) and keyword in title and (href not in seen):
            seen.add(href)
            out.append({'title': title, 'url': BASE + href})
    if not out and (not keyword):
        raise ValueError('未识别报告章节')
    return out

class _Images(HTMLParser):

    def __init__(self):
        super().__init__()
        self.depth = 0
        self.images = []

    def handle_starttag(self, t, attrs):
        a = dict(attrs)
        if t == 'div':
            if self.depth:
                self.depth += 1
            elif 'report-img' in a.get('class', '').split():
                self.depth = 1
        if self.depth and t == 'img' and a.get('src'):
            self.images.append(urljoin(BASE, a['src']))

    def handle_endtag(self, t):
        if t == 'div' and self.depth:
            self.depth -= 1

def nsfc_annual_section_detail(url):
    p = _Images()
    p.feed(_get(url))
    images = [u for u in p.images if urlparse(u).hostname == 'www.nsfc.gov.cn']
    if not images:
        raise ValueError('未识别章节图片')
    return {'url': url, 'images': images, 'note': '2024 年度报告资助情况章节以图片呈现，未 OCR、未结构化提取数值；图片和数据年份以原文为准。'}
