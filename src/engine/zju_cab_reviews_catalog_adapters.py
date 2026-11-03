"""读取浙大馆方 CAB Reviews 和三个图谱资源介绍链接。"""
import release_runtime
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse
URL = 'https://libdb.zju.edu.cn/s/lib/libtb/show/605'

def zju_cab_reviews_catalog(keyword=''):
    if not isinstance(keyword, str) or len(keyword) > 100:
        raise ValueError('关键词须不超过100字')
    r = requests.get(URL, timeout=20, allow_redirects=False)
    if r.status_code != 200:
        raise RuntimeError('馆方页面 HTTP ' + str(r.status_code))
    r.encoding = 'utf-8'
    s = BeautifulSoup(r.text, 'html.parser')
    rows = []
    for a in s.find_all('a', href=True):
        u = urlparse(a['href'])
        if u.hostname == 'www.cabidigitallibrary.org' and u.path in {'/journal/cabir', '/journal/dmpp', '/journal/dmpd', '/journal/dfb'}:
            rows.append({'title': a.get_text(' ', strip=True), 'description': a.parent.get_text(' ', strip=True), 'url': a['href']})
    if len(rows) != 4 or len({x['url'] for x in rows}) != 4:
        raise ValueError('馆方四项名单结构已改变')
    q = keyword.casefold().strip()
    return {'source': '浙大图书馆 CAB Reviews 及三个图谱说明', 'source_url': URL, 'items': [x for x in rows if q in (x['title'] + ' ' + x['description']).casefold()], 'note': '仅馆方公开的四项资源说明和链接，本地关键词筛选；非资源内部检索、实时内容或权限验证。'}
