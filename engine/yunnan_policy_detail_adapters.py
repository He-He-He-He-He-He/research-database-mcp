"""云南省政府门户政策文件正文；不提供搜索功能。"""
import release_runtime
from urllib.parse import urlsplit
import requests
from bs4 import BeautifulSoup

def detail(url):
    if not isinstance(url, str):
        raise ValueError('需要原文链接')
    p = urlsplit(url)
    try:
        valid_port = p.port in (None, 80, 443)
    except ValueError:
        valid_port = False
    if p.scheme not in ('http', 'https') or p.hostname != 'www.yn.gov.cn' or p.username or p.password or (not valid_port) or (not p.path.startswith('/zwgk/zcwj/')) or (not p.path.endswith('.html')):
        raise ValueError('仅支持云南省政府门户政策文件 HTML 链接')
    safe = 'https://www.yn.gov.cn' + p.path
    r = requests.get(safe, timeout=20, allow_redirects=False)
    r.raise_for_status()
    if r.is_redirect or 'html' not in r.headers.get('Content-Type', '').lower() or len(r.content) > 5000000:
        raise RuntimeError('页面跳转、非 HTML 或过大')
    soup = BeautifulSoup(r.content, 'html.parser')
    node = soup.select_one('.arti .TRS_UEDITOR') or soup.select_one('.arti .TRS_Editor')
    if not node:
        raise RuntimeError('正文容器未识别')
    text = node.get_text('\n', strip=True)
    if len(text) < 100:
        raise RuntimeError('正文过短，请查原网页')
    return {'url': safe, 'title': soup.title.get_text(' ', strip=True) if soup.title else None, 'text': text, 'notice': '正文来自云南省政府发布页；附件、修改与现行效力须另核。'}
