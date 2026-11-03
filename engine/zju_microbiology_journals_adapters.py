"""读取浙大图书馆 Microbiology Society 期刊说明中的名单。"""
import release_runtime
from urllib.parse import urlparse
import requests
from bs4 import BeautifulSoup
URL = 'https://libdb.zju.edu.cn/s/lib/libtb/show/2019'

def zju_microbiology_journals(keyword=''):
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
    recognized = False
    for a in box.select('a[href]'):
        p = urlparse(a['href'])
        title = ' '.join(a.get_text(' ', strip=True).split())
        if p.hostname != 'www.microbiologyresearch.org' or not p.path.startswith('/content/journal/') or (not title):
            continue
        recognized = True
        if keyword.casefold() not in title.casefold():
            continue
        items.append({'title': title, 'url': 'https://www.microbiologyresearch.org' + p.path})
    if not recognized:
        raise ValueError('未识别期刊名单，无法确认检索结果')
    return {'source': '浙大图书馆 Microbiology Society 期刊说明', 'source_url': URL, 'items': items, 'note': '馆方说明所列期刊，仅名单本地筛选；逐篇全文、投稿和费用政策未验证。'}
