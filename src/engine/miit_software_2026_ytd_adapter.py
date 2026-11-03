"""2026 software industry cumulative data: MOFCOM reprints China News reporting MIIT."""
import release_runtime
import re
import requests
from bs4 import BeautifulSoup
SOURCES = {5: 'https://dzswgf.mofcom.gov.cn/news/phone/43/2026/7/m-1782970758240.html', 7: 'https://dzswgf.mofcom.gov.cn/news/43/2026/9/1788317395322.html'}
SPECS = [('软件业务收入', '软件业务收入([0-9.]+)亿元，同比增长([0-9.]+)%', '亿元'), ('软件业利润总额', '软件业利润总额([0-9.]+)亿元，同比增长([0-9.]+)%', '亿元'), ('软件业务出口', '软件业务出口([0-9.]+)亿美元，同比增长([0-9.]+)%', '亿美元')]

def metrics(month):
    if type(month) is not int or month not in SOURCES:
        raise ValueError('month must be 5 or 7')
    u = SOURCES[month]
    with requests.get(u, timeout=(10, 45), stream=True, allow_redirects=False) as r:
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
    items = []
    for name, pattern, unit in SPECS:
        matches = []
        for p in paragraphs:
            for m in re.finditer(pattern, p):
                matches.append((m, p))
        if len(matches) != 1:
            raise ValueError('metric missing or ambiguous: ' + name)
        m, p = matches[0]
        items.append({'indicator': name, 'value': m.group(1), 'unit': unit, 'growth_percent': m.group(2), 'source_paragraph': p})
    return {'period': f'2026-01至{month:02d}', 'source': '商务部中国电子商务公共服务网转载中国新闻网关于工信部数据的报道', 'source_url': u, 'items': items, 'note': '数值为年初至月末累计，不是单月或全年；出口单位为亿美元，与收入及利润的亿元不可直接比较。同比和领域范围按原报道，跨月差额不一定等同当月值。'}
