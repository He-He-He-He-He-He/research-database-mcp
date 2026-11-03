"""浙大图书馆 Karger 电子丛书公开名单；不访问供应商。"""
import release_runtime
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse
URL = 'https://libdb.zju.edu.cn/s/lib/libtb/show/1378'

def zju_karger_series(keyword=''):
    if not isinstance(keyword, str) or len(keyword) > 100:
        raise ValueError('关键词须不超过100字')
    r = requests.get(URL, timeout=20, allow_redirects=False)
    if r.status_code != 200:
        raise RuntimeError('馆方页面 HTTP ' + str(r.status_code))
    r.encoding = 'utf-8'
    s = BeautifulSoup(r.text, 'html.parser')
    cap = s.find('caption', string=lambda x: x and 'Karger电子丛书列表' in x)
    if not cap or not cap.find_parent('table'):
        raise ValueError('未识别馆方丛书表')
    all_rows = []
    for a in cap.find_parent('table').find_all('a', href=True):
        u = urlparse(a['href'])
        if u.hostname == 'www.karger.com' and u.path.startswith('/BookSeries/Home/'):
            all_rows.append({'title': a.get_text(' ', strip=True), 'url': a['href']})
    if len(all_rows) < 1:
        raise ValueError('馆方丛书表为空')
    q = keyword.strip().casefold()
    return {'source': '浙大图书馆 Karger 电子丛书列表', 'source_url': URL, 'items': [x for x in all_rows if q in x['title'].casefold()], 'note': '馆方列表，本地关键词筛选；部分链接为馆方原始 HTTP，丛书现状及全文权限未验证。'}
