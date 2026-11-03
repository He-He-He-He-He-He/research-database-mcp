"""北京大学中国教育财政科学研究所科研简报当前页。"""
import release_runtime
import re
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
BASE = 'https://ciefr.pku.edu.cn/cbw/kyjb/index.htm'
PATTERN = re.compile('/cbw/kyjb/[a-f0-9]{32}\\.htm')

def _get(url):
    p = urlparse(url)
    if p.scheme != 'https' or p.hostname != 'ciefr.pku.edu.cn' or p.query or p.fragment or (not (p.path == '/cbw/kyjb/index.htm' or PATTERN.fullmatch(p.path))):
        raise ValueError('仅支持科研简报当前页')
    r = requests.get(url, timeout=20, allow_redirects=False)
    if r.status_code != 200:
        raise RuntimeError('上游 HTTP ' + str(r.status_code))
    r.encoding = 'utf-8'
    return r.text

def education_finance_briefs(keyword=''):
    if not isinstance(keyword, str) or len(keyword) > 100:
        raise ValueError('关键词长度不超过 100 字')
    s = BeautifulSoup(_get(BASE), 'html.parser')
    out = []
    seen = set()
    for a in s.select('a[href]'):
        u = urljoin(BASE, a['href'])
        p = urlparse(u)
        title = a.get_text(' ', strip=True)
        if p.hostname == 'ciefr.pku.edu.cn' and (not p.query) and (not p.fragment) and PATTERN.fullmatch(p.path) and (keyword in title) and (u not in seen):
            seen.add(u)
            out.append({'title': title, 'url': u})
    if not out and (not keyword):
        raise ValueError('未识别简报目录')
    return out

def education_finance_brief_detail(url):
    s = BeautifulSoup(_get(url), 'html.parser')
    area = s.select_one('.gp-content')
    if not area:
        raise ValueError('未识别简报正文')
    text = area.get_text('\n', strip=True)
    if len(text) < 100:
        raise ValueError('简报正文过短')
    return {'url': url, 'text': text, 'note': '科研简报并非微观数据；图片表格可能未转换为文本。'}
