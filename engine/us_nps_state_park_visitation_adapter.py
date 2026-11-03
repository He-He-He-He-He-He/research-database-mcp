"""US NPS official last calendar year's visitation by state and park report."""
import release_runtime
import re
import requests
from bs4 import BeautifulSoup
URL = 'https://irma.nps.gov/Stats/MvcReportViewer.aspx'
PARAMS = {'_15': 'True', '_16': 'True', '_18': 'True', '_19': 'True', '_34': 'False', '_35': 'False', '_39': '880px', '_id': '113943ca-e63d-43d4-87cc-8674fe724dac', '_m': 'Remote', '_r': '/IRMA Prod/STATS/National Reports/Visitation By State and By Park (2017 - Last Calendar Year)'}
PAGE = 'https://www.nps.gov/aboutus/visitation-numbers.htm'

def _parse(html):
    soup = BeautifulSoup(html, 'html.parser')
    text = soup.get_text(' ', strip=True)
    match = re.search('Visitation By State and by Park for Calendar Year:\\s*(\\d{4})', text, re.I)
    if not match:
        raise ValueError('report year not found')
    tables = []
    for t in soup.find_all('table'):
        trs = t.find_all('tr', recursive=False)
        if len(trs) > 100 and any(('Recreation Visitors' in r.get_text(' ', strip=True) for r in trs[:3])):
            tables.append(trs)
    if len(tables) != 1:
        raise ValueError('report table missing or ambiguous')
    rows = []
    state = None
    for tr in tables[0]:
        c = [td.get_text(' ', strip=True) for td in tr.find_all('td', recursive=False)]
        if len(c) == 5 and c[1] and (not c[2]) and (c[1] != 'State'):
            state = c[1]
        elif len(c) == 4 and state and c[1] and (not c[1].startswith('Subtotal ')):
            if not re.fullmatch('[0-9][0-9,]*', c[2]):
                raise ValueError('unexpected visitor count')
            rows.append({'state': state, 'park': c[1], 'recreation_visitors_raw': c[2], 'percent_change_raw': c[3]})
    if not rows:
        raise ValueError('empty park report')
    return (int(match.group(1)), rows)

def search(state, keyword='', limit=20, offset=0):
    if not isinstance(state, str) or not state.strip() or len(state) > 100 or (not isinstance(keyword, str)) or (len(keyword) > 120):
        raise ValueError('invalid filter')
    if any((isinstance(x, bool) or not isinstance(x, int) for x in (limit, offset))) or not 1 <= limit <= 100 or offset < 0:
        raise ValueError('invalid pagination')
    r = requests.get(URL, params=PARAMS, timeout=35)
    r.raise_for_status()
    year, rows = _parse(r.text)
    chosen = [x for x in rows if x['state'].casefold() == state.casefold() and keyword.casefold() in x['park'].casefold()]
    return {'source': r.url, 'documentation': PAGE, 'calendar_year': year, 'dataset_rows': len(rows), 'matched': len(chosen), 'offset': offset, 'limit': limit, 'rows': chosen[offset:offset + limit], 'note': 'NPS reported recreation visits by state and park, not unique visitors or all US parks. Parks crossing states can appear in multiple rows; check state allocations before aggregating. Preserve raw counts and percent changes; incomplete or revised reporting may affect comparison. This is only the latest calendar-year report; filtered locally.'}
