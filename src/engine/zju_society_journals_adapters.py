"""读取浙大图书馆美国小型学会期刊馆藏名单。"""
import release_runtime
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
URL = 'https://libdb.zju.edu.cn/s/lib/libtb/show/943'

def zju_society_journals(keyword=''):
    if not isinstance(keyword, str) or len(keyword) > 100:
        raise ValueError('关键词不超过100字')
    r = requests.get(URL, timeout=20, allow_redirects=False)
    if r.status_code != 200:
        raise RuntimeError('上游 HTTP ' + str(r.status_code))
    r.encoding = 'utf-8'
    s = BeautifulSoup(r.text, 'html.parser')
    table = s.select_one('.richbox table')
    if not table or 'ISSN' not in table.get_text(' ', strip=True):
        raise ValueError('未识别馆藏表')
    rows = []
    for tr in table.select('tbody tr'):
        c = tr.find_all('td', recursive=False)
        if len(c) != 7 or not c[0].get_text(strip=True).isdigit():
            continue
        vals = [e.get_text(' ', strip=True) for e in c]
        a = c[1].find('a', href=True)
        if keyword.casefold() in ' '.join(vals).casefold():
            rows.append({'title': vals[1], 'chinese_title': vals[2], 'publisher': vals[3], 'coverage': vals[4], 'issn': vals[5], 'frequency': vals[6], 'url': urljoin(URL, a['href']) if a else None})
    if not rows and (not keyword):
        raise ValueError('未识别期刊名单')
    return {'source': '浙大图书馆美国小型学会期刊集', 'source_url': URL, 'items': rows, 'note': '馆方名单及所列年份；各刊身份和全文权限未验证。'}
