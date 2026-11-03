"""国际海洋法法庭公开案件目录与原始文件链接。"""
import release_runtime
import re
from urllib.parse import urljoin, urlsplit
import requests
from bs4 import BeautifulSoup
BASE = 'https://www.itlos.org'

def _get(url):
    r = requests.get(url, timeout=25, allow_redirects=False)
    r.raise_for_status()
    if r.is_redirect or 'html' not in r.headers.get('Content-Type', '').lower() or len(r.content) > 5000000:
        raise RuntimeError('官方页面跳转、非 HTML 或过大')
    return BeautifulSoup(r.content, 'html.parser')

def _catalog():
    s = _get(BASE + '/en/main/cases/list-of-cases/')
    nodes = s.select('.fs-list-cases-item')
    rows = []
    if len(nodes) < 25:
        raise RuntimeError('官方目录不完整或格式变化')
    for node in nodes:
        links = node.select('h3 a')
        if len(links) != 2:
            raise RuntimeError('案件目录结构变化')
        number = links[0].get_text(' ', strip=True)
        title = links[1].get_text(' ', strip=True)
        path = links[1].get('href', '')
        p = urlsplit(urljoin(BASE, path))
        if p.scheme != 'https' or p.hostname != 'www.itlos.org' or (not p.path.startswith('/en/main/cases/')):
            raise RuntimeError('案件路径异常')
        rows.append({'number': number, 'title': title, 'url': urljoin(BASE, path)})
    return rows

def search(keyword):
    if not isinstance(keyword, str) or not keyword.strip() or len(keyword) > 200:
        raise ValueError('请输入 1–200 字英文关键词')
    items = [x for x in _catalog() if keyword.strip().casefold() in x['title'].casefold()]
    return {'source': '国际海洋法法庭案件目录', 'keyword': keyword.strip(), 'total': len(items), 'items': items, 'notice': '仅本地按官方英文案件标题匹配，不是全文搜索。'}

def documents(number):
    if not isinstance(number, str) or not re.fullmatch('(?:Case No\\. \\d+|Cases Nos \\d+ & \\d+)', number):
        raise ValueError('案件编号须与目录显示一致，例如 Case No. 25')
    candidates = [x for x in _catalog() if x['number'] == number]
    if len(candidates) != 1:
        raise ValueError('目录中未找到唯一案件编号')
    soup = _get(candidates[0]['url'])
    items = []
    seen = set()
    for a in soup.select('a[href]'):
        u = urljoin(BASE, a['href'])
        p = urlsplit(u)
        label = a.get_text(' ', strip=True)
        if p.scheme != 'https' or p.hostname != 'www.itlos.org' or (not p.path.startswith('/fileadmin/itlos/documents/cases/')) or (not p.path.lower().endswith('.pdf')) or (u in seen) or (not label):
            continue
        seen.add(u)
        items.append({'label': label, 'url': u})
    if not items:
        raise RuntimeError('未识别官方 PDF 文件链接')
    return {'source': '国际海洋法法庭案件文件', 'case': candidates[0], 'items': items, 'notice': '链接可能为判决、裁定、书状或新闻稿，应逐条核验；未读取 PDF。'}
