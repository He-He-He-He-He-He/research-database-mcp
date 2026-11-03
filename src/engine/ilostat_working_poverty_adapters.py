"""ILOSTAT SDG 1.1.1 working poverty rate, age 15+, all sexes."""
import release_runtime
import argparse
import csv
import io
import json
import re
from urllib.parse import urlencode
from ilostat_unemployment_adapters import _get
FLOW = 'DF_SDG_0111_SEX_AGE_RT'

def working_poverty(country, year):
    if not isinstance(country, str) or not re.fullmatch('[A-Z]{3}', country):
        raise ValueError('country must be a three-letter uppercase ILO area code')
    if isinstance(year, bool) or not isinstance(year, int) or (not 1950 <= year <= 2100):
        raise ValueError('invalid year')
    path = '/data/ILO,' + FLOW + '/' + country + '.A..SEX_T.AGE_YTHADULT_YGE15?' + urlencode({'startPeriod': year, 'endPeriod': year, 'format': 'csv'})
    body = _get(path)
    if body is None:
        rows = []
    else:
        reader = csv.DictReader(io.StringIO(body))
        if not reader.fieldnames or not {'REF_AREA', 'TIME_PERIOD', 'MEASURE', 'SEX', 'AGE', 'OBS_VALUE', 'SOURCE', 'UNIT_MEASURE'}.issubset(reader.fieldnames):
            raise ValueError('unexpected ILOSTAT CSV')
        rows = list(reader)
        if any((x['REF_AREA'] != country or x['TIME_PERIOD'] != str(year) or x['MEASURE'] != 'SDG_0111_RT' or (x['SEX'] != 'SEX_T') or (x['AGE'] != 'AGE_YTHADULT_YGE15') for x in rows)):
            raise ValueError('response dimensions do not match request')
    return {'source': 'ILOSTAT SDMX', 'indicator': 'SDG 1.1.1 working poverty rate', 'country': country, 'year': year, 'sex': 'all', 'age': '15+', 'unit': 'percent of employed persons', 'data': rows, 'note': 'ILOSTAT currently describes this as employed persons living below US$3 PPP per day. Source and methodology can vary; retain row SOURCE and notes and consult current ILO metadata, because the poverty line can change.'}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('country')
    p.add_argument('year', type=int)
    a = p.parse_args()
    print(json.dumps(working_poverty(a.country, a.year), ensure_ascii=False, indent=2))
if __name__ == '__main__':
    main()
