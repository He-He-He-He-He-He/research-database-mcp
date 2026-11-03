"""北师大中国居民收入调查 CHIP 公开介绍及调查资料。"""
import release_runtime
import re
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
BASE = 'https://bs.bnu.edu.cn/zgjmsrfpdcsjk/sjjs/index.html'
PATH = re.compile('/zgjmsrfpdcsjk/sjjs/(?:ljsjjs|dcsj)/[a-f0-9]{32}\\.html')

def _get(url):
    p = urlparse(url)
    if p.scheme != 'https' or p.hostname != 'bs.bnu.edu.cn' or p.query or p.fragment or (not (p.path == '/zgjmsrfpdcsjk/sjjs/index.html' or PATH.fullmatch(p.path))):
        raise ValueError('仅允许 CHIP 介绍及调查资料')
    r = requests.get(url, timeout=20, allow_redirects=False)
    if r.status_code != 200:
        raise RuntimeError('上游 HTTP ' + str(r.status_code))
    r.encoding = 'utf-8'
    return r.text

def chip_survey_documents(keyword=''):
    if not isinstance(keyword, str) or len(keyword) > 100:
        raise ValueError('关键词不超过 100 字')
    s = BeautifulSoup(_get(BASE), 'html.parser')
    out = []
    seen = set()
    recognized = False
    for a in s.select('a[href]'):
        u = urljoin(BASE, a['href'])
        p = urlparse(u)
        title = a.get_text(' ', strip=True)
        if p.hostname == 'bs.bnu.edu.cn' and PATH.fullmatch(p.path) and (not p.query) and (not p.fragment) and title:
            recognized = True
            if keyword in title and u not in seen:
                seen.add(u)
                out.append({'title': title, 'url': u})
    if not recognized:
        raise ValueError('未识别调查资料链接，无法确认检索结果')
    return out

def chip_survey_document_detail(url):
    s = BeautifulSoup(_get(url), 'html.parser')
    area = s.select_one('.list-content-crcc')
    if not area:
        raise ValueError('未识别调查资料')
    text = area.get_text('\n', strip=True)
    tables = []
    for table in area.select('table'):
        rows = [[c.get_text(' ', strip=True) for c in tr.find_all(['th', 'td'], recursive=False)] for tr in table.select('tr')]
        if rows:
            tables.append(rows)
    if len(text) < 100:
        raise ValueError('调查资料过短')
    return {'url': url, 'text': text, 'tables': tables, 'note': '公开的调查内容和样本介绍，不包含微观数据；使用条件请核对官方页面。'}
