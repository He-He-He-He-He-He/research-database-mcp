"""浙大图书馆 Cell Press 说明页期刊链接名单。"""
import release_runtime
from urllib.parse import urlparse
import requests
from bs4 import BeautifulSoup
URL = 'https://libdb.zju.edu.cn/s/lib/libtb/show/398'

def zju_cell_journals(keyword=''):
    if not isinstance(keyword, str) or len(keyword) > 100:
        raise ValueError('关键词不超过100字')
    r = requests.get(URL, timeout=20, allow_redirects=False)
    if r.status_code != 200:
        raise RuntimeError('上游 HTTP ' + str(r.status_code))
    r.encoding = 'utf-8'
    box = BeautifulSoup(r.text, 'html.parser').select_one('.richbox')
    if not box:
        raise ValueError('未识别馆方说明')
    items = []
    for a in box.select('a[href]'):
        p = urlparse(a['href'])
        title = ' '.join(a.get_text(' ', strip=True).split())
        if p.hostname != 'www.cell.com' or not title or keyword.casefold() not in title.casefold():
            continue
        items.append({'title': title, 'url': 'https://www.cell.com' + p.path + ('?' + p.query if p.query else '')})
    if not items and (not keyword):
        raise ValueError('未识别馆方期刊列表')
    return {'source': '浙大图书馆 Cell Press 期刊说明', 'source_url': URL, 'items': items, 'note': '馆方说明页所列期刊，仅名单本地筛选；未验证逐刊全文，Cell 官网曾出现安全验证。'}
