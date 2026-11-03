"""西南财经大学家庭金融调查数据通知公开目录及正文。"""
import release_runtime
import re
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
BASE = 'https://chfs.swufe.edu.cn/xwdt/tzgg.htm'
PATTERN = re.compile('/info/1041/\\d+\\.htm')

def _get(url):
    p = urlparse(url)
    if p.scheme != 'https' or p.hostname != 'chfs.swufe.edu.cn' or p.query or p.fragment or (not (p.path == '/xwdt/tzgg.htm' or PATTERN.fullmatch(p.path))):
        raise ValueError('仅支持调查中心通知公告')
    r = requests.get(url, timeout=20, allow_redirects=False)
    if r.status_code != 200:
        raise RuntimeError('上游 HTTP ' + str(r.status_code))
    r.encoding = 'utf-8'
    return r.text

def chfs_notices(keyword=''):
    if not isinstance(keyword, str) or len(keyword) > 100:
        raise ValueError('关键词不超过 100 字')
    s = BeautifulSoup(_get(BASE), 'html.parser')
    out = []
    seen = set()
    for a in s.select('a[href]'):
        url = urljoin(BASE, a['href'])
        p = urlparse(url)
        title = a.get_text(' ', strip=True)
        if p.hostname == 'chfs.swufe.edu.cn' and (not p.query) and (not p.fragment) and PATTERN.fullmatch(p.path) and (keyword in title) and (url not in seen):
            seen.add(url)
            out.append({'title': title, 'url': url})
    if not out and (not keyword):
        raise ValueError('未识别通知目录')
    return out

def chfs_notice_detail(url):
    s = BeautifulSoup(_get(url), 'html.parser')
    area = s.select_one('.article_content')
    h = s.select_one('.title_box h2')
    if not area or not h:
        raise ValueError('未识别通知正文')
    text = area.get_text('\n', strip=True)
    if len(text) < 100:
        raise ValueError('通知正文过短')
    return {'url': url, 'title': h.get_text(' ', strip=True), 'text': text, 'note': '项目通知，数据权限与申请条件以原文为准；不提交申请。'}
