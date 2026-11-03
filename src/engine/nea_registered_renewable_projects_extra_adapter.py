"""Selected official monthly renewable generation project registration tables."""
import release_runtime
import re
import requests
from bs4 import BeautifulSoup
SOURCES = {'2025-06': 'https://www.nea.gov.cn/20250730/b53696c777cc472cab6dee2e8263973a/c.html', '2025-07': 'https://www.nea.gov.cn/20250903/00f521e2481f461ab98ae7616df62f67/c.html', '2025-08': 'https://www.nea.gov.cn/20251014/33550c9bc2d544e4b00a3f490ce73991/c.html', '2026-01': 'https://www.nea.gov.cn/20260304/00841099b2d543099f5c957cb3f85b42/c.html', '2026-03': 'https://www.nea.gov.cn/20260423/ba4fc99321fa4da19624eeeb2d5e4135/c.html', '2026-04': 'https://www.nea.gov.cn/20260528/24953644c2294aa58da2ea91c0c123b3/c.html', '2026-05': 'https://www.nea.gov.cn/20260630/7d369a8776544e32adbd1bbaca577b4b/c.html', '2026-06': 'https://www.nea.gov.cn/20260720/f978dbe5fcbc4d8085a3909410b9366e/c.html'}
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
