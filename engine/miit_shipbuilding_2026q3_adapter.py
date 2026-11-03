"""2026 Q3 shipbuilding indicators, CCTV reporting MIIT data."""
import release_runtime
import re
import requests
from bs4 import BeautifulSoup
URL = 'https://jingji.cctv.cn/2026/10/23/ARTIN20EQVMWVY8Vjgvd13cP261023.shtml'

def metrics():
    with requests.get(URL, timeout=(10, 45), stream=True, allow_redirects=False) as r:
        r.raise_for_status()
        if r.is_redirect:
            raise ValueError('unexpected redirect')
        data = bytearray()
        for chunk in r.iter_content(65536):
            data.extend(chunk)
            if len(data) > 5000000:
                raise ValueError('document too large')
    soup = BeautifulSoup(bytes(data), 'html.parser')
    texts = {''.join(p.get_text(' ', strip=True).split()) for p in soup.select('p') if not p.find('p') and all((x in p.get_text() for x in ('造船完工量', '新接订单量', '手持订单量')))}
    if len(texts) != 1:
        raise ValueError('expected one unique data paragraph')
    text = texts.pop()
    shares = re.search('分别占全球市场份额的([0-9.]+)%[、，]([0-9.]+)%和([0-9.]+)%', text)
    if not shares:
        raise ValueError('global shares missing or ambiguous')
    names = ('造船完工量', '新接订单量', '手持订单量')
    items = []
    for i, name in enumerate(names):
        matches = re.findall(re.escape(name) + '([0-9.]+)万载重吨，同比增长([0-9.]+)%', text)
        if len(matches) != 1:
            raise ValueError('missing source metric: ' + name)
        value, growth = matches[0]
        items.append({'indicator': name, 'value': value, 'unit': '万载重吨', 'growth_percent': growth, 'global_share_percent': shares.group(i + 1), 'measure': '期末存量' if i == 2 else '年初累计量'})
    return {'period': '2026-01至09', 'source': '央视网报道工信部数据', 'source_url': URL, 'items': items, 'source_paragraph': text, 'note': '完工和新接为1至9月累计，手持为9月底存量。全球份额按原报道；不得将不同周期的累计与存量相加或相减作增长。'}
