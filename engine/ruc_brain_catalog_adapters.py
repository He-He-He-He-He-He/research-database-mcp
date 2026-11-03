"""中国人民大学国家治理大数据和人工智能创新平台数据目录。"""
import release_runtime
import re
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
BASE = 'https://brain.ruc.edu.cn/ydpt/sjk/'
PATTERN = re.compile('/ydpt/sjk/[a-f0-9]{32}\\.htm')

def _get(url):
    p = urlparse(url)
    if p.scheme != 'https' or p.hostname != 'brain.ruc.edu.cn' or p.query or p.fragment or (not (p.path in ('/ydpt/sjk/index.htm', '/ydpt/sjk/index1.htm') or PATTERN.fullmatch(p.path))):
        raise ValueError('仅支持人大平台指定数据库栏目')
    r = requests.get(url, timeout=20, allow_redirects=False)
    if r.status_code != 200:
        raise RuntimeError('上游 HTTP ' + str(r.status_code))
    r.encoding = 'utf-8'
    return r.text

def ruc_brain_datasets(keyword='', page=1):
    if page not in (1, 2) or not isinstance(keyword, str) or len(keyword) > 100:
        raise ValueError('页码仅支持 1–2，关键词最多 100 字')
    u = BASE + ('index.htm' if page == 1 else 'index1.htm')
    s = BeautifulSoup(_get(u), 'html.parser')
    out = []
    seen = set()
    for a in s.select('a[href]'):
        url = urljoin(u, a['href'])
        q = urlparse(url)
        title = a.get_text(' ', strip=True)
        if q.hostname == 'brain.ruc.edu.cn' and (not q.query) and (not q.fragment) and PATTERN.fullmatch(q.path) and (keyword in title) and (url not in seen):
            seen.add(url)
            out.append({'title': title, 'url': url})
    if not out and (not keyword):
        raise ValueError('未识别数据目录')
    return out

def ruc_brain_dataset_detail(url):
    s = BeautifulSoup(_get(url), 'html.parser')
    title = s.select_one('.articleTitle h3')
    cont = s.select_one('.articleCont')
    if not title or not cont:
        raise ValueError('未识别数据集介绍')
    text = cont.get_text('\n', strip=True)
    if len(text) < 100:
        raise ValueError('数据集介绍过短')
    return {'url': url, 'title': title.get_text(' ', strip=True), 'text': text, 'note': '数据集介绍页面，实际文件访问及许可请核对原站。'}
