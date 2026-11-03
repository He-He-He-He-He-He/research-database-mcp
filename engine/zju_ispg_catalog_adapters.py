"""读取浙大馆方列出的 ISPG 已订期刊与图书名单。"""
import release_runtime
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
URL = 'https://libdb.zju.edu.cn/s/lib/libtb/show/1297'

def zju_ispg_catalog(keyword=''):
    if not isinstance(keyword, str) or len(keyword) > 100:
        raise ValueError('关键词不超过100字')
    r = requests.get(URL, timeout=20, allow_redirects=False)
    if r.status_code != 200:
        raise RuntimeError('上游 HTTP ' + str(r.status_code))
    r.encoding = 'utf-8'
    s = BeautifulSoup(r.text, 'html.parser')
    head = s.find(string=lambda x: x and '图书馆订购了以下期刊和图书' in x)
    if not head:
        raise ValueError('未识别馆方名单')
    ol = head.parent.find_next_sibling('ol')
    if not ol:
        raise ValueError('未识别名单结构')
    rows = []
    for li in ol.find_all('li', recursive=False):
        a = li.find('a', href=True)
        label = li.get_text(' ', strip=True)
        if a and keyword.casefold() in label.casefold():
            rows.append({'title': a.get_text(' ', strip=True), 'label': label, 'url': urljoin(URL, a['href'])})
    if not rows and (not keyword):
        raise ValueError('馆方名单为空')
    return {'source': '浙大图书馆 ISPG 馆藏说明', 'source_url': URL, 'items': rows, 'note': '馆方公开名单，本地筛选；未验证出版商现有访问或逐项全文。'}
