"""China Statistical Yearbook 2012, table 23-4, trade union organization."""
import release_runtime
import re
import requests
from bs4 import BeautifulSoup
URL = 'https://www.stats.gov.cn/sj/ndsj/2012/html/W2304C.HTM'
COLUMNS = ['year', 'grassroots_organizations_10k', 'employees_in_unionized_units_10k', 'female_employees_in_unionized_units_10k', 'members_10k', 'female_members_10k', 'full_time_union_staff_10k']

def table():
    r = requests.get(URL, timeout=30, headers={'User-Agent': 'ResearchDatabaseToolkit/1.0'})
    r.raise_for_status()
    soup = BeautifulSoup(r.content, 'html.parser')
    t = soup.find('table')
    if t is None or '工会组织情况' not in t.get_text(' ', strip=True):
        raise ValueError('unexpected table')
    rows = []
    for tr in t.find_all('tr'):
        cells = [x.get_text(' ', strip=True) for x in tr.find_all(['td', 'th'], recursive=False)]
        if len(cells) == 7 and re.fullmatch('\\d{4}', cells[0]):
            rows.append(dict(zip(COLUMNS, [int(cells[0])] + [float(x.replace(',', '')) if x else None for x in cells[1:]])))
    if not rows:
        raise ValueError('no year rows found')
    return {'source_url': URL, 'table': '23-4 工会组织情况', 'note': '2003年起工会基层组织数统计口径有所调整。', 'rows': rows}

def year(year):
    matches = [r for r in table()['rows'] if r['year'] == year]
    return matches[0] if matches else None
