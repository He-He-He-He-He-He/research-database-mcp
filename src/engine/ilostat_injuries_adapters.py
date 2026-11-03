"""ILOSTAT SDG 8.8.1 occupational injury rates per 100,000 workers."""
import release_runtime
import argparse
import csv
import io
import json
import re
from urllib.parse import urlencode
from ilostat_unemployment_adapters import _get
KINDS = {'fatal': ('DF_SDG_F881_SEX_MIG_RT', 'SDG_F881_RT'), 'nonfatal': ('DF_SDG_N881_SEX_MIG_RT', 'SDG_N881_RT')}
SEX = {'total': 'SEX_T', 'female': 'SEX_F', 'male': 'SEX_M'}

def injury_rate(country, year, kind='fatal', sex='total'):
    if not isinstance(country, str) or not re.fullmatch('[A-Z]{3}', country):
        raise ValueError('country must be three uppercase letters')
    if isinstance(year, bool) or not isinstance(year, int) or (not 1950 <= year <= 2100):
        raise ValueError('invalid year')
    if kind not in KINDS or sex not in SEX:
        raise ValueError('invalid kind or sex')
    flow, measure = KINDS[kind]
    path = '/data/ILO,' + flow + '/' + country + '.A..' + SEX[sex] + '.MIG_STATUS_TOTAL?' + urlencode({'startPeriod': year, 'endPeriod': year, 'format': 'csv'})
    body = _get(path)
    if body is None:
        rows = []
    else:
        reader = csv.DictReader(io.StringIO(body))
        if not reader.fieldnames or not {'REF_AREA', 'FREQ', 'MEASURE', 'SEX', 'MIG', 'TIME_PERIOD', 'OBS_VALUE', 'SOURCE'}.issubset(reader.fieldnames):
            raise ValueError('unexpected ILOSTAT CSV')
        rows = list(reader)
        if any((x['REF_AREA'] != country or x['FREQ'] != 'A' or x['MEASURE'] != measure or (x['SEX'] != SEX[sex]) or (x['MIG'] != 'MIG_STATUS_TOTAL') or (x['TIME_PERIOD'] != str(year)) for x in rows)):
            raise ValueError('response dimensions do not match request')
    return {'source': 'ILOSTAT SDMX', 'indicator': 'SDG 8.8.1 occupational injuries', 'country': country, 'year': year, 'kind': kind, 'sex': sex, 'migrant_status': 'total', 'unit': 'cases per 100,000 workers', 'data': rows, 'note': 'Coverage, reporting systems and inclusion of occupational diseases vary by country; inspect source and indicator notes before comparison.'}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('country')
    p.add_argument('year', type=int)
    p.add_argument('--kind', choices=KINDS, default='fatal')
    p.add_argument('--sex', choices=SEX, default='total')
    a = p.parse_args()
    print(json.dumps(injury_rate(a.country, a.year, a.kind, a.sex), ensure_ascii=False, indent=2))
if __name__ == '__main__':
    main()
