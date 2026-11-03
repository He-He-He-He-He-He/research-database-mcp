"""National Energy Administration provincial wind grid connection tables, 2017–2018."""
import release_runtime
import requests
from bs4 import BeautifulSoup
SOURCES = {'2017q3': 'https://www.nea.gov.cn/2017-10/31/c_136717648.htm', '2018q3': 'https://www.nea.gov.cn/2018-10/30/c_137569222.htm', '2018': 'https://www.nea.gov.cn/2019-01/28/c_137780779.htm'}

def catalog():
    return [{'period': k, 'url': u} for k, u in SOURCES.items()]

def table(period, region=''):
    if period not in SOURCES:
        raise ValueError('period must be 2017q3, 2018q3, or 2018')
    if not isinstance(region, str) or len(region) > 100:
        raise ValueError('invalid region')
    u = SOURCES[period]
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
    ts = [t for t in soup.find_all('table') if not t.find('table') and len(t.find_all('tr')) > 30]
    if len(ts) != 1:
        raise ValueError('expected one leaf data table')
    rows = []
    for n, tr in enumerate(ts[0].find_all('tr'), 1):
        cells = [{'text': c.get_text(' ', strip=True), 'rowspan': int(c.get('rowspan', 1)), 'colspan': int(c.get('colspan', 1))} for c in tr.find_all(['td', 'th'], recursive=False)]
        rows.append({'row': n, 'cells': cells})
    q = ''.join(region.split())
    matches = [r for r in rows if q in ''.join((''.join(c['text'].split()) for c in r['cells']))]
    if region and (not matches):
        matches = []
    return {'period': period, 'source': '国家能源局风电并网运行情况', 'source_url': u, 'headers': rows[:3], 'rows': matches, 'matched_rows': len(matches), 'note': '原表保留空白和原值。累计并网容量、发电量及利用小时数是不同指标；表头未显示单位，可结合公报正文中全国总量核查：容量万千瓦、发电量亿千瓦时、利用小时数小时。2018年表末列是各地区承诺的弃风率控制目标，而不是实际弃风率；跨期比较核对统计时间与范围。'}
