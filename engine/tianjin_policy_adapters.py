"""天津政务网政府文件栏目分页及原文；不提供跨页搜索。"""
import release_runtime
import re
from urllib.parse import urljoin, urlsplit
import requests
from bs4 import BeautifulSoup
BASE = 'https://www.tj.gov.cn/zwgk/szfwj/'

def list_page(page=1):
    if isinstance(page, bool) or not isinstance(page, int) or (not 1 <= page <= 67):
        raise ValueError('页码须为 1–67，实际范围可能随更新变化')
    r = requests.get(BASE + ('index_' + str(page - 1) + '.html' if page > 1 else ''), timeout=20, allow_redirects=False)
    r.raise_for_status()
    if r.is_redirect:
        raise RuntimeError('栏目页面跳转')
    s = BeautifulSoup(r.content, 'html.parser')
    rows = s.select('.list-circle-red .list-item')
    items = []
    if not rows:
        raise RuntimeError('官方栏目结果为空或格式变化')
    for row in rows:
        a = row.select_one('a.list-item-con')
        title = row.select_one('.item-title')
        cat = row.select_one('.item-catagory')
        date = row.select_one('.list-item-date')
        if not all((a, title, cat, date)):
            raise RuntimeError('栏目格式变化')
        u = urljoin(BASE, a.get('href', ''))
        p = urlsplit(u)
        if p.hostname != 'www.tj.gov.cn' or not p.path.startswith('/zwgk/szfwj/'):
            raise RuntimeError('文件链接范围异常')
        items.append({'title': title.get_text(' ', strip=True), 'category': cat.get_text(' ', strip=True), 'date': date.get_text(' ', strip=True), 'url': u})
    return {'source': '天津市政府文件栏目', 'page': page, 'items': items, 'notice': '栏目分页浏览；含不同效力文件及批复。'}

def detail(url):
    if not isinstance(url, str):
        raise ValueError('需要文件链接')
    p = urlsplit(url)
    try:
        port = p.port in (None, 80, 443)
    except ValueError:
        port = False
    if p.scheme not in ('http', 'https') or p.hostname != 'www.tj.gov.cn' or p.username or p.password or (not port) or (not re.fullmatch('/zwgk/szfwj/[A-Za-z0-9_]+/\\d{6}/t\\d+_\\d+\\.html', p.path)):
        raise ValueError('仅支持天津政府文件栏目正文链接')
    safe = 'https://www.tj.gov.cn' + p.path
    r = requests.get(safe, timeout=20, allow_redirects=False)
    r.raise_for_status()
    if r.is_redirect or 'html' not in r.headers.get('Content-Type', '').lower() or len(r.content) > 5000000:
        raise RuntimeError('页面跳转、非 HTML 或过大')
    s = BeautifulSoup(r.content, 'html.parser')
    node = s.select_one('.article_content .TRS_UEDITOR')
    if not node:
        raise RuntimeError('正文容器未识别')
    text = node.get_text('\n', strip=True)
    if len(text) < 100:
        raise RuntimeError('正文过短，请查看原站附件')
    return {'url': safe, 'title': s.title.get_text(' ', strip=True) if s.title else None, 'text': text, 'notice': '请核对附件及当前法律效力。'}
