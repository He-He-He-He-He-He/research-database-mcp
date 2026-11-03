"""ILOSTAT SDG 1.3.1 population covered by at least one social protection benefit."""
import release_runtime
import argparse
import csv
import io
import json
import re
from urllib.parse import urlencode
from ilostat_unemployment_adapters import _get
FLOW = 'DF_SDG_0131_SEX_SOC_RT'
SEX = {'total': 'SEX_T', 'female': 'SEX_F', 'male': 'SEX_M'}

def protection_coverage(country, year, sex='total'):
    if not isinstance(country, str) or not re.fullmatch('[A-Z]{3}', country):
        raise ValueError('country must be three uppercase letters')
    if isinstance(year, bool) or not isinstance(year, int) or (not 1950 <= year <= 2100):
        raise ValueError('invalid year')
    if sex not in SEX:
        raise ValueError('sex must be total, female or male')
    path = '/data/ILO,' + FLOW + '/' + country + '.A..' + SEX[sex] + '.SOC_CONTIG_TOTAL?' + urlencode({'startPeriod': year, 'endPeriod': year, 'format': 'csv'})
    body = _get(path)
    if body is None:
        rows = []
    else:
        reader = csv.DictReader(io.StringIO(body))
        if not reader.fieldnames or not {'REF_AREA', 'FREQ', 'MEASURE', 'SEX', 'SOC', 'TIME_PERIOD', 'OBS_VALUE', 'UNIT_MEASURE', 'SOURCE'}.issubset(reader.fieldnames):
            raise ValueError('unexpected ILOSTAT CSV')
        rows = list(reader)
        if any((x['REF_AREA'] != country or x['FREQ'] != 'A' or x['MEASURE'] != 'SDG_0131_RT' or (x['SEX'] != SEX[sex]) or (x['SOC'] != 'SOC_CONTIG_TOTAL') or (x['TIME_PERIOD'] != str(year)) or (x['UNIT_MEASURE'] != 'PT') for x in rows)):
            raise ValueError('response dimensions do not match request')
    return {'source': 'ILOSTAT SDMX', 'indicator': 'SDG 1.3.1 at least one social protection benefit', 'country': country, 'year': year, 'sex': sex, 'unit': 'percent of population', 'data': rows, 'note': 'Population covered by at least one social protection benefit; not coverage of every benefit. Data sources, coverage and survey years vary by country.'}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('country')
    p.add_argument('year', type=int)
    p.add_argument('--sex', choices=SEX, default='total')
    a = p.parse_args()
    print(json.dumps(protection_coverage(a.country, a.year, a.sex), ensure_ascii=False, indent=2))
if __name__ == '__main__':
    main()
