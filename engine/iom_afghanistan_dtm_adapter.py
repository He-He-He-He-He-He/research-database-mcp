"""IOM Afghanistan displacement observations, published on OCHA HDX."""
import release_runtime
import csv, io
import requests
META = 'https://data.humdata.org/api/3/action/package_show'
RESOURCE = 'bc3fe8eb-af75-4b4c-ac96-9ca9c96e05de'

def observations(level='0', year=None, limit=20):
    if level not in ('0', '1', '2'):
        raise ValueError('level must be 0, 1, or 2')
    if year is not None and (isinstance(year, bool) or not isinstance(year, int) or (not 1950 <= year <= 2100)):
        raise ValueError('invalid year')
    if isinstance(limit, bool) or not isinstance(limit, int) or (not 1 <= limit <= 100):
        raise ValueError('invalid limit')
    s = requests.Session()
    m = s.get(META, params={'id': 'afg-iom-dtm-from-api'}, timeout=30)
    m.raise_for_status()
    data = m.json()
    if data.get('success') is not True:
        raise ValueError('HDX metadata error')
    package = data['result']
    resources = [x for x in package['resources'] if x.get('id') == RESOURCE]
    if len(resources) != 1 or package.get('organization', {}).get('title') != 'International Organization for Migration (IOM)':
        raise ValueError('IOM resource metadata changed')
    url = resources[0]['url']
    if not url.startswith('https://data.humdata.org/'):
        raise ValueError('unexpected resource host')
    response = s.get(url, timeout=60)
    response.raise_for_status()
    reader = csv.DictReader(io.StringIO(response.content.decode('utf-8-sig')))
    if not {'adminLevel', 'yearReportingDate', 'numPresentIdpInd'}.issubset(reader.fieldnames or []):
        raise ValueError('unexpected schema')
    rows = [row for row in reader if row['adminLevel'] == level and (year is None or row['yearReportingDate'] == str(year))]
    return {'dataset': package['title'], 'resource_id': RESOURCE, 'metadata_modified': package.get('metadata_modified'), 'level': level, 'year': year, 'matched': len(rows), 'returned': len(rows[:limit]), 'rows': rows[:limit], 'note': 'Snapshots are not additive across dates, rounds, reasons, and nested administrative levels.'}
