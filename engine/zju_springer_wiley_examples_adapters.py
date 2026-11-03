"""浙大馆方页面列出的 Springer 东欧期刊和 Wiley 工具书示例。"""
import release_runtime
from urllib.parse import urlparse
import requests
from bs4 import BeautifulSoup

def _examples(identifier, host, keyword):
    if not isinstance(keyword, str) or len(keyword) > 100:
        raise ValueError('关键词不超过100字')
    url = 'https://libdb.zju.edu.cn/s/lib/libtb/show/' + identifier
    r = requests.get(url, timeout=20, allow_redirects=False)
    if r.status_code != 200:
        raise RuntimeError('上游 HTTP ' + str(r.status_code))
    r.encoding = 'utf-8'
    box = BeautifulSoup(r.text, 'html.parser').select_one('.richbox')
    if not box:
        raise ValueError('未识别馆方说明')
    rows = []
    recognized = False
    for a in box.select('a[href]'):
        p = urlparse(a['href'])
        title = a.get_text(' ', strip=True)
        if p.hostname != host or not title:
            continue
        recognized = True
        if keyword.casefold() not in title.casefold():
            continue
        rows.append({'title': title, 'url': 'https://' + host + p.path + ('?' + p.query if p.query else '')})
    if not recognized:
        raise ValueError('未识别示例列表，无法确认检索结果')
    return {'source_url': url, 'items': rows, 'note': '馆方说明中的部分示例，仅本地筛选；非完整订购清单或全文权限验证。'}

def zju_springer_eastern_examples(keyword=''):
    return _examples('1322', 'link.springer.com', keyword)

def zju_wiley_reference_examples(keyword=''):
    return _examples('1041', 'onlinelibrary.wiley.com', keyword)
