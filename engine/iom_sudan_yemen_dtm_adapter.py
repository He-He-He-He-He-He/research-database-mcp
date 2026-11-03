"""IOM Sudan and Yemen DTM public datasets hosted by OCHA HDX."""
import release_runtime
import csv, io
import requests
META = 'https://data.humdata.org/api/3/action/package_show'
DATASETS = {'SDN': ('sdn-iom-dtm-from-api', 'ca01bea5-8b89-4838-8cdc-37fec81be136'), 'YEM': ('yem-iom-dtm-from-api', 'a4108594-21e3-4c35-8f55-0374693a4c1b')}

def observations(country, level='0', year=None, limit=20):
    if country not in DATASETS:
        raise ValueError('country must be SDN or YEM')
    if level not in ('0', '1', '2'):
        raise ValueError('level must be 0, 1 or 2')
    if year is not None and (isinstance(year, bool) or not isinstance(year, int) or (not 1950 <= year <= 2100)):
        raise ValueError('invalid year')
    if isinstance(limit, bool) or not isinstance(limit, int) or (not 1 <= limit <= 100):
        raise ValueError('invalid limit')
    dataset, resource = DATASETS[country]
    s = requests.Session()
    r = s.get(META, params={'id': dataset}, timeout=30)
    r.raise_for_status()
    d = r.json()
    if d.get('success') is not True:
        raise ValueError('HDX metadata error')
    p = d['result']
    rs = [x for x in p['resources'] if x.get('id') == resource]
    if len(rs) != 1 or p.get('organization', {}).get('title') != 'International Organization for Migration (IOM)':
        raise ValueError('IOM metadata changed')
    url = rs[0]['url']
    if not url.startswith('https://data.humdata.org/'):
        raise ValueError('unexpected resource host')
    r = s.get(url, timeout=90)
    r.raise_for_status()
    reader = csv.DictReader(io.StringIO(r.content.decode('utf-8-sig')))
    if not {'adminLevel', 'yearReportingDate', 'numPresentIdpInd'}.issubset(reader.fieldnames or []):
        raise ValueError('unexpected CSV schema')
    rows = [x for x in reader if x['adminLevel'] == level and (year is None or x['yearReportingDate'] == str(year))]
    return {'dataset': p['title'], 'resource_id': resource, 'dataset_date': p.get('dataset_date'), 'metadata_modified': p.get('metadata_modified'), 'matched': len(rows), 'returned': len(rows[:limit]), 'rows': rows[:limit], 'note': 'Snapshots are not additive across rounds, causes, dates or administrative levels.'}
