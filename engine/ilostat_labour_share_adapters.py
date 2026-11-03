"""ILOSTAT modelled labour income share as percentage of GDP."""
import release_runtime
import argparse
import csv
import io
import json
import re
from urllib.parse import urlencode
from ilostat_unemployment_adapters import _get
FLOW = 'DF_LAP_2GDP_NOC_RT'

def labour_share(country, year):
    if not isinstance(country, str) or not re.fullmatch('[A-Z]{3}', country):
        raise ValueError('country must be three uppercase letters')
    if isinstance(year, bool) or not isinstance(year, int) or (not 1950 <= year <= 2100):
        raise ValueError('invalid year')
    path = '/data/ILO,' + FLOW + '/' + country + '.A..?' + urlencode({'startPeriod': year, 'endPeriod': year, 'format': 'csv'})
    body = _get(path)
    if body is None:
        rows = []
    else:
        reader = csv.DictReader(io.StringIO(body))
        if not reader.fieldnames or not {'REF_AREA', 'FREQ', 'MEASURE', 'TIME_PERIOD', 'OBS_VALUE', 'OBS_STATUS', 'UNIT_MEASURE', 'SOURCE'}.issubset(reader.fieldnames):
            raise ValueError('unexpected ILOSTAT CSV')
        rows = list(reader)
        if any((x['REF_AREA'] != country or x['FREQ'] != 'A' or x['MEASURE'] != 'LAP_2GDP_RT' or (x['TIME_PERIOD'] != str(year)) or (x['UNIT_MEASURE'] != 'PT') for x in rows)):
            raise ValueError('response dimensions do not match request')
    return {'source': 'ILOSTAT SDMX, ILO modelled estimates', 'indicator': 'Labour income share as percentage of GDP', 'country': country, 'year': year, 'unit': 'percent of GDP', 'data': rows, 'note': 'Includes labour income of employees and self-employed workers. Model estimates may be revised; preserve status and source fields.'}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('country')
    p.add_argument('year', type=int)
    a = p.parse_args()
    print(json.dumps(labour_share(a.country, a.year), ensure_ascii=False, indent=2))
if __name__ == '__main__':
    main()
