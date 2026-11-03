"""IARC CI5plus 2024 registry counts: official archived ZIP, locally filtered."""
import release_runtime
import csv
import io
import json
import requests
import zipfile
URL = 'https://gco.iarc.who.int/media/ci5/data/ci5plus/CI5plus_Summary.zip'
DOC = 'https://ci5.aws-csu.iarc.who.int/ci5plus/download/'
HELP = 'https://ci5.iarc.who.int/ci5plus/help/'

def _archive():
    r = requests.get(URL, timeout=90)
    r.raise_for_status()
    return (r, zipfile.ZipFile(io.BytesIO(r.content)))

def _csv(z, name):
    return csv.DictReader(io.TextIOWrapper(z.open(name), encoding='utf-8-sig', newline=''))

def catalog(kind, keyword='', offset=0, limit=50):
    if kind not in ('registry', 'cancer'):
        raise ValueError('kind must be registry or cancer')
    if not isinstance(offset, int) or isinstance(offset, bool) or offset < 0:
        raise ValueError('invalid offset')
    if not isinstance(limit, int) or isinstance(limit, bool) or (not 1 <= limit <= 500):
        raise ValueError('invalid limit')
    r, z = _archive()
    try:
        records = [v for v in _csv(z, 'id_dict.csv' if kind == 'registry' else 'cancer_dict.csv') if not keyword or keyword.strip().casefold() in ' '.join(v.values()).casefold()]
        return {'source': URL, 'documentation': DOC, 'download_bytes': len(r.content), 'metadata': json.loads(z.read('info.json')), 'kind': kind, 'total': len(records), 'offset': offset, 'limit': limit, 'rows': records[offset:offset + limit]}
    finally:
        z.close()

def observations(registry, cancer, year=None, sex=None, offset=0, limit=50):
    if not isinstance(registry, str) or not registry.isdigit() or (not isinstance(cancer, str)) or (not cancer.isdigit()):
        raise ValueError('registry and cancer must be digit codes')
    if year is not None and (not isinstance(year, int) or isinstance(year, bool) or (not 1900 <= year <= 2100)):
        raise ValueError('invalid year')
    if sex is not None and str(sex) not in ('1', '2'):
        raise ValueError('sex must be raw code 1 or 2')
    if not isinstance(offset, int) or isinstance(offset, bool) or offset < 0:
        raise ValueError('invalid offset')
    if not isinstance(limit, int) or isinstance(limit, bool) or (not 1 <= limit <= 500):
        raise ValueError('invalid limit')
    r, z = _archive()
    try:
        registries = [x for x in _csv(z, 'id_dict.csv') if x['id_code'] == registry]
        cancers = [x for x in _csv(z, 'cancer_dict.csv') if x['cancer_code'] == cancer]
        if not registries or not cancers:
            raise ValueError('unknown registry or cancer code')
        total = 0
        rows = []
        for row in _csv(z, 'data.csv'):
            if row['id_code'] != registry or row['cancer_code'] != cancer:
                continue
            if year is not None and row['year'] != str(year):
                continue
            if sex is not None and row['sex'] != str(sex):
                continue
            if offset <= total < offset + limit:
                rows.append(row)
            total += 1
        return {'source': URL, 'documentation': DOC, 'methods': HELP, 'download_bytes': len(r.content), 'metadata': json.loads(z.read('info.json')), 'registry': registries[0], 'cancer': cancers[0], 'total_rows': total, 'offset': offset, 'limit': limit, 'rows': rows, 'notes': ['Observed registry case counts and population-years, not national cancer estimates; registries can overlap and differ in coverage.', 'Raw age and sex codes are retained. The archive description calls age code 2 “4-9” while IARC help lists standard groups as 5–9; do not silently resolve this discrepancy.', 'Archive 2024 version 1.1, registry periods vary and are historical; missing data do not imply zero. This command downloads 15 MB and streams a roughly 120 MB CSV for filtering.']}
    finally:
        z.close()
