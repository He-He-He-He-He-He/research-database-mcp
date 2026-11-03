"""青海省交通运输厅转载省政府文件栏目，仅目录。"""
import release_runtime
from urllib.parse import urlsplit
import requests
from bs4 import BeautifulSoup
BASE = 'https://jtyst.qinghai.gov.cn/jtyst/jtxx/szfwj/'

def list_page(page=1):
    if isinstance(page, bool) or not isinstance(page, int) or (not 1 <= page <= 27):
        raise ValueError('页码须为 1–27，实际页数随官网更新变化')
    r = requests.get(BASE + ('index.html' if page == 1 else f'0c14a096-{page}.html'), timeout=20, allow_redirects=False)
    r.raise_for_status()
    if r.is_redirect or 'html' not in r.headers.get('Content-Type', '').lower() or len(r.content) > 5000000:
        raise RuntimeError('栏目页面跳转、格式异常或过大')
    s = BeautifulSoup(r.content, 'html.parser')
    rows = s.select('ul.list li:has(a[istitle])')
    items = []
    if not rows:
        raise RuntimeError('栏目为空或格式变化')
    for row in rows:
        a = row.select_one('a[istitle]')
        t = row.select_one('span')
        u = a.get('href', '')
        p = urlsplit(u)
        if p.hostname != 'www.qinghai.gov.cn' or not p.path.startswith('/xxgk/xxgk/fd/zfwj/'):
            raise RuntimeError('文件链接不属于省政府栏目')
        items.append({'title': a.get('title'), 'date': t.get_text(' ', strip=True) if t else None, 'url': u})
    return {'source': '青海省交通运输厅转载的省政府文件栏目', 'page': page, 'items': items, 'notice': '仅栏目目录；原文链接由该网站提供，原文不可用时不可据此判断政策效力。'}
