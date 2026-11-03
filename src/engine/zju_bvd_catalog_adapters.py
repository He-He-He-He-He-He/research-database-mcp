"""读取浙大图书馆 BvD 系列馆藏名单。"""
import release_runtime
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse
URL = 'https://libdb.zju.edu.cn/s/lib/libtb/show/1100'

def zju_bvd_catalog(keyword=''):
    if not isinstance(keyword, str) or len(keyword) > 100:
        raise ValueError('关键词不超过100字')
    r = requests.get(URL, timeout=20, allow_redirects=False)
    if r.status_code != 200:
        raise RuntimeError('上游 HTTP ' + str(r.status_code))
    r.encoding = 'utf-8'
    s = BeautifulSoup(r.text, 'html.parser')
    head = s.find(string=lambda x: x and '已订购的BvD系列数据库' in x)
    if not head:
        raise ValueError('未识别馆方名单')
    ul = head.parent.find_next_sibling('ul')
    if not ul:
        raise ValueError('未识别名单结构')
    rows = []
    for li in ul.find_all('li', recursive=False):
        a = li.find('a', href=True)
        label = li.get_text(' ', strip=True)
        if a and keyword.casefold() in label.casefold():
            p = urlparse(a['href'])
            url = 'https://libdb.zju.edu.cn' + p.path if p.hostname == 'libdb.zju.edu.cn' else a['href']
            rows.append({'title': a.get_text(' ', strip=True), 'label': label, 'url': url})
    if not rows and (not keyword):
        raise ValueError('馆方名单为空')
    return {'source': '浙大图书馆 BvD 馆藏说明', 'source_url': URL, 'items': rows, 'note': '馆方公开名单；具体产品登录状态和数据访问须逐项验证。'}
