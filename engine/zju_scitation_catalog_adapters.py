"""读取浙大 Scitation 说明页所列关联馆藏。"""
import release_runtime
import re
import requests
from bs4 import BeautifulSoup
URL = 'https://libdb.zju.edu.cn/s/lib/libtb/show/395'

def zju_scitation_catalog(keyword=''):
    if not isinstance(keyword, str) or len(keyword) > 100:
        raise ValueError('关键词不超过100字')
    r = requests.get(URL, timeout=20, allow_redirects=False)
    if r.status_code != 200:
        raise RuntimeError('上游 HTTP ' + str(r.status_code))
    r.encoding = 'utf-8'
    s = BeautifulSoup(r.text, 'html.parser')
    box = s.select_one('.richbox ul')
    if not box:
        raise ValueError('未识别馆方列表')
    rows = []
    for li in box.find_all('li', recursive=False):
        a = li.find('a', href=True)
        label = li.get_text(' ', strip=True)
        if not a or keyword.casefold() not in label.casefold():
            continue
        match = re.search('/s/lib/libtb/show/(\\d+)', a['href'])
        if not match:
            continue
        rows.append({'title': a.get_text(' ', strip=True), 'label': label, 'url': 'https://libdb.zju.edu.cn/s/lib/libtb/show/' + match.group(1)})
    if not rows and (not keyword):
        raise ValueError('馆方列表为空')
    return {'source': '浙大图书馆 Scitation 说明', 'source_url': URL, 'items': rows, 'note': '馆方列出的关联馆藏，并非 Scitation 全部期刊；检索需平台注册，逐刊全文权限未验证。'}
