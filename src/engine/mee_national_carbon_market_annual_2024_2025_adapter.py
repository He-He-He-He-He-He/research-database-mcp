"""MEE national emissions trading market annual summaries for 2024 and 2025."""
import release_runtime
import re
import requests
from bs4 import BeautifulSoup
SOURCES = {2024: 'https://www.mee.gov.cn/ywgz/ydqhbh/syqhbh/202501/t20250105_1099975.shtml', 2025: 'https://www.mee.gov.cn/ywgz/ydqhbh/wsqtkz/202601/t20260101_1139528.shtml'}

def catalog():
    return [{'year': y, 'url': u} for y, u in sorted(SOURCES.items(), reverse=True)]

def report(year):
    if type(year) is not int or year not in SOURCES:
        raise ValueError('year must be 2024 or 2025')
    with requests.get(SOURCES[year], timeout=(10, 35), stream=True, allow_redirects=False) as r:
        r.raise_for_status()
        if r.is_redirect:
            raise ValueError('unexpected redirect')
        raw = bytearray()
        for c in r.iter_content(65536):
            raw.extend(c)
            if len(raw) > 3000000:
                raise ValueError('response too large')
    soup = BeautifulSoup(bytes(raw), 'html.parser')
    body = soup.select_one('.TRS_Editor')
    if not body:
        raise ValueError('source body missing')
    text = body.get_text('', strip=True)
    text = re.sub('\\s+', '', text)
    patterns = {'covered_entities': ('(?:发电行业)?重点排放单位共计([0-9.]+)家', '家'), 'trading_days': ('市场共运行([0-9.]+)个交易日', '日'), 'cumulative_cea_volume': ('全国碳排放权交易市场配额累计成交量([0-9.]+)亿吨', '亿吨'), 'cumulative_cea_value': ('配额累计成交量[0-9.]+亿吨，累计成交额([0-9.]+)亿元', '亿元'), 'year_cea_volume': (f'{year}年全年配额成交量([0-9.]+)亿吨', '亿吨'), 'year_cea_value': (f'{year}年全年配额成交量[0-9.]+亿吨[^。]{{0,30}}?成交额([0-9.]+)亿元', '亿元'), 'year_end_price': ('年底收盘价为([0-9.]+)元/吨', '元/吨')}
    metrics = {}
    for key, (pat, unit) in patterns.items():
        found = list(re.finditer(pat, text))
        if len(found) == 1:
            m = found[0]
            metrics[key] = {'value': m.group(1), 'unit': unit, 'source_excerpt': m.group(0)}
    if not metrics:
        raise ValueError('no recognized metrics')
    return {'source': '生态环境部全国碳排放权交易市场年度通报', 'year': year, 'url': SOURCES[year], 'metrics': metrics, 'source_text': text, 'note': '累计成交指市场启动以来截至年末，全年成交指当年；配额与自愿减排市场不同，覆盖行业逐年变化。' + ('2024年全年成交额原通报为181.14亿元，同部后续答复为180.44亿元，差异原因待核。' if year == 2024 else '')}
