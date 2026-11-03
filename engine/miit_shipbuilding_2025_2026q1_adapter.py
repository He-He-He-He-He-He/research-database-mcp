"""Official Chinese shipbuilding indicators for 2025 and 2026 Q1."""
import release_runtime
import re
import requests
from bs4 import BeautifulSoup
SOURCES = {'2025': 'https://www.miit-eidc.org.cn/art/2026/2/2/art_1618_12122.html', '2026q1': 'https://www.miit-eidc.org.cn/art/2026/5/9/art_1618_12296.html'}

def metrics(period):
    if period not in SOURCES:
        raise ValueError('period must be 2025 or 2026q1')
    url = SOURCES[period]
    with requests.get(url, timeout=(10, 45), stream=True, allow_redirects=False) as r:
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
        raise ValueError('expected one unique source paragraph')
    text = texts.pop()
    items = []
    for name in ('造船完工量', '新接订单量', '手持订单量'):
        m = re.search(re.escape(name) + '([0-9.]+)万载重吨，同比(增长|下降)([0-9.]+)%，占世界总量的([0-9.]+)%', text)
        if not m:
            raise ValueError('missing source metric: ' + name)
        items.append({'indicator': name, 'value': m.group(1), 'unit': '万载重吨', 'growth_direction': m.group(2), 'growth_percent': m.group(3), 'global_share_percent': m.group(4), 'measure': '期末存量' if name == '手持订单量' else '年初累计量'})
    return {'period': period, 'source': '工业和信息化部装备工业发展中心转载工信部装备工业二司', 'source_url': url, 'items': items, 'source_paragraph': text, 'note': '完工和新接为该期累计，手持是期末存量；国际份额按载重吨，不是修正总吨。不同周期的累计量不得直接相减成同比。'}
