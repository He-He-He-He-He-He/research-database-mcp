"""JODI Oil official year-file access; returns original monthly observations."""
import release_runtime
import csv
import io
import re
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
PAGE = 'https://www.jodidata.org/oil/database/data-downloads.aspx'
CODE_GUIDE = 'https://www.jodidata.org/_resources/files/downloads/oil-data/jodi-wdb-short-long-names.pdf'
COUNTRY_NOTES = 'https://www.jodidata.org/_resources/files/downloads/oil-data/jodi-oil-country-note.xlsx'

def _get(url, maxbytes):
    with requests.get(url, stream=True, timeout=(15, 50)) as r:
        r.raise_for_status()
        parts = []
        size = 0
        for chunk in r.iter_content(65536):
            size += len(chunk)
            if size > maxbytes:
                raise RuntimeError('JODI response exceeds limit')
            parts.append(chunk)
    return b''.join(parts)

def catalogue():
    soup = BeautifulSoup(_get(PAGE, 3000000), 'html.parser')
    entries = []
    for a in soup.find_all('a', href=True):
        u = urljoin(PAGE, a['href'])
        p = urlparse(u)
        match = re.fullmatch('/_resources/files/downloads/oil-data/annual-csv/(primary|secondary)/(?:primaryyear|secondaryyear)?(\\d{4})\\.csv', p.path)
        if p.scheme == 'https' and p.netloc == 'www.jodidata.org' and match:
            entries.append({'product_group': match.group(1), 'year': match.group(2), 'url': u})
    if not entries or len({(e['product_group'], e['year']) for e in entries}) != len(entries):
        raise RuntimeError('JODI annual file list missing or ambiguous')
    return {'source': 'Joint Organisations Data Initiative (JODI), coordinated by IEF', 'source_page': PAGE, 'code_guide': CODE_GUIDE, 'country_notes': COUNTRY_NOTES, 'items': entries, 'note': 'Year files contain monthly observations; primary and secondary product groups differ.'}

def data(group, year, country, product='', flow='', unit='', month='', offset=0, limit=20):
    if group not in ('primary', 'secondary') or not isinstance(year, str) or (not re.fullmatch('\\d{4}', year)) or (not isinstance(country, str)) or (not re.fullmatch('[A-Z]{2}', country)):
        raise ValueError('Specify primary/secondary, four-digit year, two-letter area')
    for v in (product, flow, unit):
        if not isinstance(v, str) or (v and (not re.fullmatch('[A-Z0-9]{1,20}', v))):
            raise ValueError('Invalid code filter')
    if month and (not isinstance(month, str) or not re.fullmatch('0[1-9]|1[0-2]', month)):
        raise ValueError('month must be 01–12')
    if not isinstance(offset, int) or isinstance(offset, bool) or offset < 0 or (not isinstance(limit, int)) or isinstance(limit, bool) or (not 1 <= limit <= 100):
        raise ValueError('Invalid pagination')
    meta = catalogue()
    match = [e for e in meta['items'] if e['product_group'] == group and e['year'] == year]
    if len(match) != 1:
        raise ValueError('Year file absent from official JODI catalogue')
    raw = _get(match[0]['url'], 30000000)
    f = io.StringIO(raw.decode('utf-8-sig'), newline='')
    reader = csv.DictReader(f)
    expected = {'REF_AREA', 'TIME_PERIOD', 'ENERGY_PRODUCT', 'FLOW_BREAKDOWN', 'UNIT_MEASURE', 'OBS_VALUE', 'ASSESSMENT_CODE'}
    if set(reader.fieldnames or []) != expected:
        raise RuntimeError('Unexpected JODI CSV schema')
    out = []
    count = 0
    for row in reader:
        if row['REF_AREA'] != country or not row['TIME_PERIOD'].startswith(year + '-') or (month and row['TIME_PERIOD'] != year + '-' + month) or (product and row['ENERGY_PRODUCT'] != product) or (flow and row['FLOW_BREAKDOWN'] != flow) or (unit and row['UNIT_MEASURE'] != unit):
            continue
        if offset <= count < offset + limit:
            out.append(row)
        count += 1
    return {'source': 'Joint Organisations Data Initiative (JODI), coordinated by IEF', 'source_page': PAGE, 'download_url': match[0]['url'], 'code_guide': CODE_GUIDE, 'country_notes': COUNTRY_NOTES, 'matched': count, 'offset': offset, 'items': out, 'note': 'Year files contain monthly series, not annual totals. Values, units, missing markers and assessment codes are preserved as strings. Codes 1/2/3/4 respectively denote reasonable comparability, use with caution, not assessed, and under verification in the 2017 code guide; consult current country notes and definitions. Overlapping units or products must not be summed.'}
