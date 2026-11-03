"""GFDRR ThinkHazard public hazard classifications and division codes."""
import release_runtime
import csv
import io
import re
import requests
from bs4 import BeautifulSoup
BASE = 'https://thinkhazard.org/en/report/'
DOC = 'https://gfdrr.github.io/thinkhazardmethods/'
INDEX = 'https://raw.githubusercontent.com/GFDRR/thinkhazardmethods/master/source/download/'
HAZARDS = ('EQ', 'VO', 'TS', 'CY', 'FL', 'UF', 'CF', 'LS', 'EH', 'WF', 'DR', 'VA', 'DG')

def divisions(level, keyword='', offset=0, limit=20):
    if level not in ('ADM0', 'ADM1', 'ADM2'):
        raise ValueError('invalid administrative level')
    if not isinstance(offset, int) or isinstance(offset, bool) or offset < 0:
        raise ValueError('invalid offset')
    if not isinstance(limit, int) or isinstance(limit, bool) or (not 1 <= limit <= 500):
        raise ValueError('invalid limit')
    u = INDEX + level + '_TH.csv'
    r = requests.get(u, timeout=45)
    r.raise_for_status()
    rows = list(csv.DictReader(io.StringIO(r.content.decode('utf-8-sig')), delimiter=';'))
    found = [x for x in rows if not keyword or keyword.strip().casefold() in ' '.join(x.values()).casefold()]
    return {'source': u, 'documentation': DOC, 'level': level, 'total_matches': len(found), 'offset': offset, 'limit': limit, 'rows': found[offset:offset + limit], 'note': 'Division list is the historical directory linked by GFDRR documentation; codes and administrative names should be verified against the current report.'}

def report(division, hazard=''):
    if not isinstance(division, str) or not re.fullmatch('[0-9]{1,12}', division):
        raise ValueError('invalid division code')
    if hazard and hazard not in HAZARDS:
        raise ValueError('unknown hazard code')
    u = BASE + division + ('/' + hazard if hazard else '') + '.json'
    r = requests.get(u, timeout=45)
    r.raise_for_status()
    j = r.json()
    if hazard and (not isinstance(j, dict)):
        raise ValueError('unexpected hazard detail response')
    if not hazard and (not isinstance(j, list)):
        raise ValueError('unexpected report response')
    page = requests.get(BASE + division, timeout=45)
    page.raise_for_status()
    s = BeautifulSoup(page.text, 'html.parser')
    title = s.title.get_text(' ', strip=True) if s.title else None
    return {'source': u, 'report_page': BASE + division, 'report_title': title, 'documentation': DOC, 'data': j, 'notes': ['Hazard classifications are screening-level and administrative-area-wide, not a site-specific engineering study or a forecast of actual losses.', 'Thresholds and underlying data differ by hazard; no-data, no-hazard and low are distinct. Check source descriptions and model vintage before use.', 'This is the legacy thinkhazard.org service; classifications can differ from newer int.thinkhazard.org reports and are not guaranteed current. Third-party source datasets in detailed reports may have different access or reuse restrictions. Neither the latest source-data timestamp nor current project-specific conditions are guaranteed.']}
