"""MOJ historical administrative reconsideration and litigation HTML tables."""
import release_runtime
import requests
from bs4 import BeautifulSoup
BASE = 'https://www.moj.gov.cn/pub/sfbgw/zwxxgk/fdzdgknr/fdzdgknrtjxx/'
PATHS = {2013: '201403/t20140324_350040.html', 2016: '201812/t20181231_350043.html', 2018: '202103/t20210331_350048.html', 2019: '202009/t20200929_392195.html', 2021: '202209/t20220902_462830.html', 2022: '202307/t20230711_482419.html'}

def tables(year):
    if year not in PATHS:
        raise ValueError('available years: 2013, 2016, 2018, 2019, 2021, 2022')
    url = BASE + PATHS[year]
    r = requests.get(url, timeout=30)
    r.raise_for_status()
    soup = BeautifulSoup(r.content, 'html.parser')
    result = []
    for t in soup.find_all('table'):
        p = next((x for x in t.find_all_previous('p') if not x.find('table') and x.get_text('', strip=True)), None)
        rows = []
        for row in t.find_all('tr'):
            cells = [{'text': c.get_text('', strip=True), 'rowspan': int(c.get('rowspan', 1)), 'colspan': int(c.get('colspan', 1))} for c in row.find_all(['td', 'th'], recursive=False)]
            if cells:
                rows.append(cells)
        if rows:
            result.append({'caption': p.get_text('', strip=True) if p else '', 'rows': rows})
    if not result:
        raise ValueError('no HTML tables found')
    return {'year': year, 'source': '中华人民共和国司法部', 'source_url': url, 'tables': result}
