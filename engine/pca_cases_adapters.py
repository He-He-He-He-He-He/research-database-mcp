"""常设仲裁法院获准公开的案件目录和文件链接；不代表全部案件。"""
import release_runtime
import re
from urllib.parse import urljoin, urlsplit
import requests
from bs4 import BeautifulSoup
BASE = 'https://pca.int'

def _get(path):
    r = requests.get(BASE + path, timeout=25, allow_redirects=False)
    r.raise_for_status()
    if r.is_redirect or 'html' not in r.headers.get('Content-Type', '').lower() or len(r.content) > 5000000:
        raise RuntimeError('页面跳转、非 HTML 或过大')
    return BeautifulSoup(r.content, 'html.parser')

def search(keyword):
    if not isinstance(keyword, str) or not keyword.strip() or len(keyword) > 200:
        raise ValueError('请输入 1–200 字英文关键词')
    s = _get('/en/cases/')
    links = s.select('.fold-out-content ul.pointer-list li a')
    items = []
    if len(links) < 100:
        raise RuntimeError('公开案件目录不完整或格式变化')
    for a in links:
        path = a.get('href', '')
        m = re.fullmatch('(\\d+)/', path)
        title = a.get_text(' ', strip=True)
        if not m:
            continue
        if keyword.strip().casefold() in title.casefold():
            items.append({'title': title, 'case_id': int(m.group(1)), 'url': f'{BASE}/en/cases/{m.group(1)}/'})
    return {'source': '常设仲裁法院公开案件列表', 'keyword': keyword.strip(), 'total': len(items), 'items': items, 'notice': '只含获准公开的案件，已结案件仅部分；按标题本地匹配，不是文档全文搜索。'}

def documents(case_id):
    if isinstance(case_id, bool) or not isinstance(case_id, int) or (not 1 <= case_id <= 999999):
        raise ValueError('案件编号须为 1–999999 整数')
    s = _get(f'/en/cases/{case_id}/')
    items = []
    for node in s.select('.downloads .download'):
        label = node.select_one('.download-label')
        links = node.select_one('.download-links')
        a = links.find('a', href=True) if links else None
        if not label or not a:
            continue
        u = a['href']
        p = urlsplit(u)
        if p.scheme != 'https' or p.hostname not in ('pcacases.com', 'www.pcacases.com', 'files.pca-cpa.org', 'docs.pca-cpa.org'):
            continue
        items.append({'label': label.get_text(' ', strip=True), 'url': u, 'description': links.get_text(' ', strip=True)})
    if not items:
        raise RuntimeError('此案未识别可公开的文件链接或页面结构变化')
    return {'source': '常设仲裁法院案件页', 'case_id': case_id, 'items': items, 'notice': '文件可能为书状、裁决、程序文件等；仅列链接，不保证下载可用或案卷完整。'}
