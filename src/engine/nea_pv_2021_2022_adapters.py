"""National Energy Administration provincial solar capacity tables, 2021–2022."""
import release_runtime
import requests
from bs4 import BeautifulSoup
SOURCES = {'2021q1': 'https://www.nea.gov.cn/2021-04/27/c_139910029.htm', '2021': 'https://www.nea.gov.cn/2022-03/09/c_1310508114.htm', '2022h1': 'https://www.nea.gov.cn/2022-07/29/c_1310647830.htm'}

def catalog():
    return [{'period': k, 'url': u} for k, u in SOURCES.items()]

def table(period, region=''):
    if period not in SOURCES:
        raise ValueError('period must be 2021q1, 2021, or 2022h1')
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
    return {'period': period, 'source': '国家能源局光伏发电建设运行情况', 'source_url': u, 'unit': '万千瓦', 'headers': rows[:3], 'rows': matches, 'matched_rows': len(matches), 'note': '原表保持空白和原值，2021一季度列为累计及新增且全国总计累计值原文写作“258 50”，含空格且未擅自改写；2021全年与2022上半年列为新增及累计，户用为分布式的其中项。容量是装机而非发电量；数据口径及退运修订须核原文。'}
