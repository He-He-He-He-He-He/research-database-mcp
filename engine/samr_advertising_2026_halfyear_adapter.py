"""SAMR 2026 H1 advertising metrics, reported by Xinhua."""
import release_runtime
import re
import requests
from bs4 import BeautifulSoup
URL = 'https://www.xinhuanet.com/fortune/20260807/f839886620494ee887454779f8c8940c/c.html'

def summary():
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
    paragraphs = [''.join(p.get_text(' ', strip=True).split()) for p in soup.select('p') if not p.find('p')]
    specs = [('头部企事业单位广告业务收入', '头部企事业单位共实现收入([0-9.]+)亿元，同比增长([0-9.]+)%', ('value', 'growth_percent')), ('互联网广告发布收入', '互联网广告发布收入([0-9.]+)亿元，同比增长([0-9.]+)%，占全部广告发布收入的([0-9.]+)%', ('value', 'growth_percent', 'share_percent')), ('北京上海广东浙江江苏福建广告业务收入合计', '广告业务收入合计([0-9.]+)亿元，同比增长([0-9.]+)%，占全国总量的([0-9.]+)%', ('value', 'growth_percent', 'share_percent'))]
    out = []
    for name, pattern, fields in specs:
        hits = [(p, m) for p in paragraphs if (m := re.search(pattern, p))]
        if len(hits) != 1:
            raise ValueError('missing or ambiguous metric: ' + name)
        p, m = hits[0]
        row = {'indicator': name, 'unit': '亿元', 'source_paragraph': p}
        row.update(dict(zip(fields, m.groups())))
        out.append(row)
    return {'period': '2026-H1', 'source_url': URL, 'source': '新华社报道市场监管总局数据', 'items': out, 'note': '头部企事业单位上半年范围不同于2025全年事业单位及规模以上企业；互联网为广告发布收入，不等于广告业务收入。不能直接相减或未经核实计算同比。'}
