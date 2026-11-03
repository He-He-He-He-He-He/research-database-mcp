"""ILOSTAT SDG 8.2.1 annual output per worker growth, constant 2021 PPP."""
import release_runtime
import argparse
import csv
import io
import json
import re
from urllib.parse import urlencode
from ilostat_unemployment_adapters import _get
FLOW = 'DF_SDG_B821_NOC_RT'

def productivity_growth(country, year):
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
        if not reader.fieldnames or not {'REF_AREA', 'FREQ', 'MEASURE', 'TIME_PERIOD', 'OBS_VALUE', 'UNIT_MEASURE', 'SOURCE'}.issubset(reader.fieldnames):
            raise ValueError('unexpected ILOSTAT CSV')
        rows = list(reader)
        if any((x['REF_AREA'] != country or x['FREQ'] != 'A' or x['MEASURE'] != 'SDG_B821_RT' or (x['TIME_PERIOD'] != str(year)) or (x['UNIT_MEASURE'] != 'PT') for x in rows)):
            raise ValueError('response dimensions do not match request')
    return {'source': 'ILOSTAT SDMX', 'indicator': 'SDG 8.2.1 annual growth in output per worker', 'country': country, 'year': year, 'unit': 'percent change', 'GDP_basis': 'constant 2021 international dollars at PPP', 'data': rows, 'note': 'Growth in output per employed person, not GDP growth or the level of output. Preserve source and status fields; series may be model estimates and revised.'}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('country')
    p.add_argument('year', type=int)
    a = p.parse_args()
    print(json.dumps(productivity_growth(a.country, a.year), ensure_ascii=False, indent=2))
if __name__ == '__main__':
    main()
