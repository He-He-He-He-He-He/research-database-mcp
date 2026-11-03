"""INPE TerraBrasilis PRODES Legal Amazon deforestation rate series."""
import release_runtime
import hashlib
import re
from urllib.parse import urljoin, urlparse
import requests
from bs4 import BeautifulSoup
DASHBOARD = 'https://terrabrasilis.dpi.inpe.br/app/dashboard/deforestation/biomes/legal_amazon/rates'
HOST = 'https://terrabrasilis.dpi.inpe.br'
FILES = HOST + '/app/prodes/dashboard/deforestation/files/'
NOTES = ['PRODES monitors clear-cut deforestation in the Legal Amazon, not all Brazil, all Amazon biome countries, or the whole tropical forest.', 'Each labelled year ends July 31 and begins the previous August 1; area is km² per monitoring year, not a calendar-year count or a percentage.', 'The displayed overall area is an explicitly calculated sum of nine source regional values. Numeric regional identifiers are preserved without assigning names.', 'The latest Amazon figure can be an estimate based on priority images, with a consolidated estimate later; series can be revised. Current data are not a historical release snapshot.', 'PRODES annual rates are distinct from DETER near-real-time alerts and must not be compared as if identical measures.']

def _get(url):
    r = requests.get(url, timeout=60)
    r.raise_for_status()
    return r

def query(start, end):
    if type(start) is not int or type(end) is not int or (not 1988 <= start <= end <= 2100):
        raise ValueError('Invalid monitoring end-year range')
    r = _get(DASHBOARD)
    s = BeautifulSoup(r.text, 'html.parser')
    scripts = []
    for a in s.select('script[src]'):
        u = urljoin(DASHBOARD, a['src'])
        p = urlparse(u)
        if p.scheme == 'https' and p.hostname == 'terrabrasilis.dpi.inpe.br' and re.fullmatch('/app/dashboard/deforestation/app\\.[a-f0-9]+\\.js', p.path):
            scripts.append(u)
    if len(scripts) != 1:
        raise ValueError('Cannot identify official dashboard application')
    js = _get(scripts[0]).content.decode('utf-8', 'replace')
    names = set(re.findall('rates20\\d{2}\\.json', js))
    if len(names) != 1:
        raise ValueError('Cannot identify current INPE rates file')
    url = FILES + names.pop()
    r = _get(url)
    j = r.json()
    if j.get('name') != 'PRODES LEGAL AMAZON' or j.get('clazz') != 'deforestation_rates' or (not isinstance(j.get('periods'), list)):
        raise ValueError('Unexpected INPE dataset')
    rows = []
    for p in j['periods']:
        y = p['endDate']['year']
        if not start <= y <= end:
            continue
        f = p['features']
        ids = [x.get('loiname') for x in f]
        if len(f) != 9 or len(set(ids)) != 9 or any((x.get('loi') != 1 or len(x.get('areas', [])) != 1 or x['areas'][0].get('type') != 1 or (type(x['areas'][0].get('area')) not in (int, float)) for x in f)):
            raise ValueError('Unexpected INPE region structure; cannot sum')
        rows.append({'monitoring_end_year': y, 'period_start': p['startDate'], 'period_end': p['endDate'], 'regional_values_raw': f, 'calculated_sum_km2': sum((x['areas'][0]['area'] for x in f))})
    return {'source': url, 'dashboard': DASHBOARD, 'http_last_modified': r.headers.get('Last-Modified'), 'sha256': hashlib.sha256(r.content).hexdigest(), 'notes': NOTES, 'records': rows}
