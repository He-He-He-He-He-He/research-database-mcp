"""Read official HTML tables from selected China fishery bulletins."""
import release_runtime
import requests
from bs4 import BeautifulSoup
from moa_fisheries_bulletin_history_adapter import SOURCES
YEARS = (2020, 2021, 2023, 2024, 2025)
NAMES = ('全国水产养殖产量', '全国水产捕捞产量', '全国海水养殖面积', '全国淡水养殖面积')

def catalog():
    return [{'year': year, 'url': SOURCES[year], 'tables': list(NAMES)} for year in YEARS]

def tables(year):
    if type(year) is not int or year not in YEARS:
        raise ValueError('supported years: 2020, 2021, 2023, 2024, 2025')
    url = SOURCES[year]
    with requests.get(url, timeout=(10, 30), stream=True, allow_redirects=False) as response:
        response.raise_for_status()
        if response.is_redirect:
            raise ValueError('unexpected redirect')
        raw = bytearray()
        for chunk in response.iter_content(65536):
            raw.extend(chunk)
            if len(raw) > 3000000:
                raise ValueError('response exceeds size limit')
    soup = BeautifulSoup(bytes(raw), 'html.parser')
    body = soup.select_one('.TRS_Editor')
    found = body.select('table') if body else []
    if len(found) != 4:
        raise ValueError('source no longer has expected four tables')
    result = []
    for index, (name, table) in enumerate(zip(NAMES, found)):
        rows = []
        for tr in table.select('tr'):
            rows.append([{'text': cell.get_text('', strip=True), 'rowspan': int(cell.get('rowspan', 1)), 'colspan': int(cell.get('colspan', 1))} for cell in tr.find_all(['th', 'td'], recursive=False)])
        if not rows or not any(('指标' in c['text'] for c in rows[0])):
            raise ValueError('table header not recognized')
        result.append({'title': f'{year}年' + name, 'base_unit': '万吨' if index < 2 else '千公顷', 'rows': rows})
    return {'source': '农业农村部全国渔业经济统计公报', 'year': year, 'url': url, 'tables': result, 'note': '保留原始单元格与合并信息；数值、单位及适用范围请结合原文核对，空白并非零。'}
