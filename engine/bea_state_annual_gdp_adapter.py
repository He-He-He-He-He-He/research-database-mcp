"""BEA regional annual state GDP summary, SAGDP1 current release."""
import release_runtime
import csv, io, re, zipfile
import requests
from bs4 import BeautifulSoup
URL = 'https://apps.bea.gov/regional/zip/SAGDP.zip'
PAGE = 'https://www.bea.gov/data/gdp/gdp-state'
NOTE = 'US Bureau of Economic Analysis SAGDP1 state annual GDP summary, latest release may be revised. Five-digit GeoFIPS selects a source area, including national/regional aggregates as well as states; aggregates overlap. Each row has distinct unit and concept: chained real GDP is not current-dollar GDP or the quantity index. GDP and its component lines overlap; do not sum all rows. Preserve source strings, signs, missing/disclosure flags and footnotes; chained-dollar values are not additive in general. Empty year selection is not zero. Release information and methodology should be checked at the BEA source; not GDP for every city/county.'

def query(geofips, start, end, line=None, session=None):
    if not isinstance(geofips, str) or not re.fullmatch('\\d{5}', geofips):
        raise ValueError('GeoFIPS must be 5 digits')
    if type(start) is not int or type(end) is not int or (not 1900 <= start <= end <= 2100):
        raise ValueError('invalid year range')
    if line is not None and (type(line) is not int or not 1 <= line <= 8):
        raise ValueError('line must be 1..8')
    r = (session or requests).get(URL, timeout=65)
    r.raise_for_status()
    raw = r.content
    if len(raw) > 30000000:
        raise ValueError('archive too large')
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        entries = [x for x in z.infolist() if re.fullmatch('SAGDP1__ALL_AREAS_\\d{4}_\\d{4}\\.csv', x.filename)]
        if len(entries) != 1 or entries[0].file_size > 5000000:
            raise ValueError('unexpected SAGDP1 archive structure')
        info = entries[0]
        try:
            footinfo = z.getinfo('SAGDP1__Footnotes.html')
        except KeyError:
            raise ValueError('missing source footnotes')
        if footinfo.file_size > 1000000:
            raise ValueError('source footnotes too large')
        footnotes = BeautifulSoup(z.read(footinfo), 'html.parser').get_text(' ', strip=True)
        if not footnotes:
            raise ValueError('source footnotes empty')
        with z.open(info) as f:
            reader = csv.DictReader(io.TextIOWrapper(f, encoding='utf-8-sig', newline=''))
            required = {'GeoFIPS', 'GeoName', 'TableName', 'LineCode', 'Description', 'Unit'}
            if not reader.fieldnames or not required.issubset(reader.fieldnames):
                raise ValueError('missing source headers')
            years = [k for k in reader.fieldnames if re.fullmatch('\\d{4}', k)]
            if not years:
                raise ValueError('no year headers')
            items = []
            foot = []
            for row in reader:
                if row.get('TableName') == 'SAGDP1':
                    code = (row.get('GeoFIPS') or '').strip().strip('"')
                    if not re.fullmatch('\\d{5}', code):
                        raise ValueError('invalid data geography')
                    if code == geofips and (line is None or row.get('LineCode') == str(line)):
                        items.append({'geofips': code, 'geofips_raw': row['GeoFIPS'], 'geoname': row['GeoName'], 'table': row['TableName'], 'line_code': row['LineCode'], 'industry_classification': row.get('IndustryClassification'), 'description': row['Description'], 'unit_raw': row['Unit'], 'values': {y: row[y] for y in years if start <= int(y) <= end}})
                elif row.get('GeoFIPS') and (not row.get('GeoName')):
                    foot.append(row['GeoFIPS'])
            if len({x['line_code'] for x in items}) != len(items):
                raise ValueError('duplicate line for selected geography')
    return {'source': URL, 'dataset_page': PAGE, 'archive_bytes': len(raw), 'source_csv': info.filename, 'geofips': geofips, 'start': start, 'end': end, 'available_years': [years[0], years[-1]], 'items': items, 'source_notes_raw': foot, 'source_footnotes_text': footnotes, 'note': NOTE}
