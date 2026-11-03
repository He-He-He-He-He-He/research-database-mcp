"""读取浙大图书馆主题教育资源汇总中的资源名称与入口。"""
import release_runtime
import re
from urllib.parse import urljoin
import requests
from bs4 import BeautifulSoup
URL = 'https://libdb.zju.edu.cn/s/lib/libtb/show/1833'

def zju_topic_resources(keyword=''):
    if not isinstance(keyword, str) or len(keyword) > 100:
        raise ValueError('关键词不超过100字')
    r = requests.get(URL, timeout=20, allow_redirects=False)
    if r.status_code != 200:
        raise RuntimeError('上游 HTTP ' + str(r.status_code))
    r.encoding = 'utf-8'
    s = BeautifulSoup(r.text, 'html.parser')
    box = s.select_one('.richbox')
    if not box:
        raise ValueError('未识别馆方汇总')
    items = []
    recognized = False
    for p in box.find_all('p', recursive=False):
        text = p.get_text(' ', strip=True)
        a = p.find('a', href=True)
        if not a or not re.match('^\\s*\\d+\\s*、', text):
            continue
        title = a.get_text(' ', strip=True)
        if not title:
            continue
        recognized = True
        if keyword.casefold() not in text.casefold():
            continue
        items.append({'title': title, 'url': urljoin(URL, a['href']), 'label': text})
    if not recognized:
        raise ValueError('未识别资源名单，无法确认检索结果')
    return {'source': '浙大图书馆主题教育文献资源汇总', 'source_url': URL, 'items': items, 'note': '馆方公开资源清单，仅本地筛选；不代表入口可访问或正文已获授权。'}
