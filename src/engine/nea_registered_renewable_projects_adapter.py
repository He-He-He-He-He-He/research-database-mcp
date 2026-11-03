"""Selected official monthly renewable generation project registration tables."""
import release_runtime
import re
import requests
from bs4 import BeautifulSoup
SOURCES = {'2025-09': 'https://www.nea.gov.cn/20251031/1a51e15ddf60490b804bec26a4589b21/c.html', '2025-10': 'https://www.nea.gov.cn/20251202/c0d8867f172e49ebae6d600d5ceec6cf/c.html', '2025-11': 'https://www.nea.gov.cn/20251231/a6f4a56fd3534e208cc27143af651cb4/c.html', '2025-12': 'https://www.nea.gov.cn/20260203/63c4d0afe6b94250a62e8792cdb28e3b/c.html', '2026-07': 'https://www.nea.gov.cn/20260904/324fdc3e4908431392b82d19ab10de6b/c.html', '2026-08': 'https://www.nea.gov.cn/20260923/aaadb598d4cc4c0a92585bfd26c8728e/c.html'}
HEADERS = ['地区', '风电', '集中式光伏发电', '工商业分布式光伏发电', '生物质发电', '合计']

def catalog():
    return [{'month': month, 'source_url': url} for month, url in sorted(SOURCES.items(), reverse=True)]

def table(month):
    if month not in SOURCES:
        raise ValueError('month must be one of the listed sources')
    url = SOURCES[month]
    with requests.get(url, timeout=(10, 30), stream=True, allow_redirects=False) as response:
        response.raise_for_status()
        if response.is_redirect:
            raise ValueError('unexpected redirect')
        raw = bytearray()
        for chunk in response.iter_content(65536):
            raw.extend(chunk)
            if len(raw) > 3000000:
                raise ValueError('response too large')
    soup = BeautifulSoup(bytes(raw), 'html.parser')
    candidates = []
    for table in soup.select('table'):
        rows = table.find_all('tr', recursive=False)
        if not rows:
            tbody = table.find('tbody', recursive=False)
            rows = tbody.find_all('tr', recursive=False) if tbody else []
        if not rows:
            continue
        header = [c.get_text('', strip=True).replace('\u3000', '') for c in rows[0].find_all(['td', 'th'], recursive=False)]
        if header == HEADERS:
            candidates.append(rows)
    if len(candidates) != 1:
        raise ValueError('expected exactly one project table')
    entries = []
    for row in candidates[0][1:]:
        cells = [c.get_text('', strip=True) for c in row.find_all(['td', 'th'], recursive=False)]
        if len(cells) != 6 or not cells[0] or any((not re.fullmatch('\\d+', x) for x in cells[1:])):
            raise ValueError('unexpected source row; do not infer missing values')
        entries.append(dict(zip(HEADERS, [cells[0]] + [int(x) for x in cells[1:]])))
    if len(entries) != 32 or entries[0]['地区'] != '全国':
        raise ValueError('unexpected region coverage')
    return {'source': '国家能源局', 'source_url': url, 'month': month, 'unit': '个', 'headers': HEADERS, 'rows': entries, 'note': '本月新增建档立卡项目数，不含户用光伏；非装机容量、发电量或全部项目数。'}
