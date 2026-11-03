"""International IDEA Global State of Democracy indices version 10."""
import release_runtime
import csv
import io
import re
import requests
URL = 'https://www.idea.int/democracytracker/idea-mod/download-proxy'
SOURCE = 'https://www.idea.int/sites/default/files/2026-06/gsod_indices_v10.csv'
ATTRIBUTES = {'representation', 'rights', 'rule_law', 'participation'}

def query(country_code, year_from, year_to, *, attribute='representation', limit=100):
    if not re.fullmatch('[A-Z]{3}', country_code) or attribute not in ATTRIBUTES:
        raise ValueError('invalid country code or attribute')
    if any((type(x) is not int for x in (year_from, year_to, limit))) or not 1975 <= year_from <= year_to <= 2025 or (not 1 <= limit <= 100):
        raise ValueError('invalid years or limit')
    with requests.get(URL, params={'url': SOURCE}, timeout=90, stream=True) as r:
        r.raise_for_status()
        body = r.raw.read(35000001, decode_content=True)
    if len(body) > 35000000:
        raise ValueError('source CSV exceeds size limit')
    rows = csv.DictReader(io.StringIO(body.decode('utf-8-sig')))
    cols = [attribute + s for s in ('_est', '_l', '_u')]
    if not set(['year', 'iso3c', 'country_name'] + cols).issubset(rows.fieldnames or []):
        raise ValueError('unexpected CSV columns')
    found = []
    for row in rows:
        if row['iso3c'] != country_code or not row['year'].isdigit() or (not year_from <= int(row['year']) <= year_to):
            continue

        def num(v):
            return None if v in ('', 'NA') else float(v)
        found.append({'country': row['country_name'], 'iso3': row['iso3c'], 'year': int(row['year']), 'estimate': num(row[cols[0]]), 'lower': num(row[cols[1]]), 'upper': num(row[cols[2]]), 'raw_values': {k: row[k] for k in cols}})
    return {'source': 'International IDEA Global State of Democracy Indices v10', 'url': SOURCE, 'attribute': attribute, 'total_matches': len(found), 'limit': limit, 'truncated': len(found) > limit, 'records': found[:limit], 'note': 'When truncated increase limit up to 100 or narrow the year range. Multi-source model estimates with uncertainty bounds, not official national statistics or independent raw observations. Bounds are preserved as published even outside 0–1; raw_values retain source strings, including missing markers. Redistribution and commercial-use permission have not been verified.'}
