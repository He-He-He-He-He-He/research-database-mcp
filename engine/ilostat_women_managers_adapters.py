"""ILOSTAT SDG 5.5.2 women as a proportion of managers, annual series."""
import release_runtime
import argparse
import csv
import io
import json
import re
from urllib.parse import urlencode
from ilostat_unemployment_adapters import _get
FLOW = 'DF_SDG_T552_NOC_RT'

def women_managers(country, year):
    if not isinstance(country, str) or not re.fullmatch('[A-Z]{3}', country):
        raise ValueError('country must be a three-letter uppercase ILO area code')
    if isinstance(year, bool) or not isinstance(year, int) or (not 1950 <= year <= 2100):
        raise ValueError('invalid year')
    path = '/data/ILO,' + FLOW + '/' + country + '.A..?' + urlencode({'startPeriod': year, 'endPeriod': year, 'format': 'csv'})
    body = _get(path)
    if body is None:
        rows = []
    else:
        reader = csv.DictReader(io.StringIO(body))
        if not reader.fieldnames or not {'REF_AREA', 'FREQ', 'MEASURE', 'TIME_PERIOD', 'OBS_VALUE', 'UNIT_MEASURE', 'SOURCE'}.issubset(reader.fieldnames):
            raise ValueError('unexpected ILOSTAT CSV')
        rows = list(reader)
        if any((x['REF_AREA'] != country or x['FREQ'] != 'A' or x['MEASURE'] != 'SDG_T552_RT' or (x['TIME_PERIOD'] != str(year)) or (x['UNIT_MEASURE'] != 'PT') for x in rows)):
            raise ValueError('response dimensions do not match request')
    return {'source': 'ILOSTAT SDMX', 'indicator': 'SDG 5.5.2 proportion of women in managerial positions', 'flow': FLOW, 'country': country, 'year': year, 'unit': 'percent of managers', 'data': rows, 'note': 'All managerial positions, not solely senior and middle management; source survey and definitions may differ, so retain upstream notes. This is not the proportion of women who are managers.'}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('country')
    p.add_argument('year', type=int)
    a = p.parse_args()
    print(json.dumps(women_managers(a.country, a.year), ensure_ascii=False, indent=2))
if __name__ == '__main__':
    main()
