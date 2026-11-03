"""读取浙大 Landes Bioscience 馆方期刊名单，不访问供应商。"""
import release_runtime
import requests
from bs4 import BeautifulSoup
URL = 'https://libdb.zju.edu.cn/s/lib/libtb/show/1276'

def zju_landes_journals(keyword=''):
    if not isinstance(keyword, str) or len(keyword) > 100:
        raise ValueError('关键词须不超过100字')
    r = requests.get(URL, timeout=20, allow_redirects=False)
    if r.status_code != 200:
        raise RuntimeError('馆方页面 HTTP ' + str(r.status_code))
    r.encoding = 'utf-8'
    s = BeautifulSoup(r.text, 'html.parser')
    cap = s.find('caption', string=lambda x: x and '期刊列表' in x)
    if not cap or not cap.find_parent('table'):
        raise ValueError('未识别馆方期刊表')
    rows = []
    for td in cap.find_parent('table').find_all('td'):
        title = td.get_text(' ', strip=True)
        a = td.find('a', href=True)
        if title:
            rows.append({'title': title, 'url': a['href'] if a else None})
    if not rows:
        raise ValueError('馆方期刊表为空')
    q = keyword.strip().casefold()
    return {'source': '浙大图书馆 Landes Bioscience 期刊列表', 'source_url': URL, 'items': [v for v in rows if q in v['title'].casefold()], 'note': '馆方页面列示期刊名单，部分无链接或原始链接为 HTTP；非文章检索、全文或当前权限验证。'}
