"""NOAA CO-OPS observed six-minute coastal water levels, in metres and GMT."""
import release_runtime
import argparse
import datetime as dt
import json
import re
import subprocess
from urllib.parse import urlencode
BASE = 'https://api.tidesandcurrents.noaa.gov/api/prod/datagetter'

def water_level(station, begin_date, end_date, datum='MLLW'):
    if not isinstance(station, str) or not re.fullmatch('\\d{7}', station):
        raise ValueError('station must be a seven-digit NOAA station ID')
    if datum not in ('MLLW', 'MHHW', 'MSL', 'NAVD', 'STND'):
        raise ValueError('unsupported datum')
    try:
        start, end = (dt.datetime.strptime(x, '%Y-%m-%d').date() for x in (begin_date, end_date))
    except (ValueError, TypeError):
        raise ValueError('dates must be YYYY-MM-DD') from None
    if start > end or (end - start).days > 30:
        raise ValueError('date range must be ordered and at most 31 days inclusive')
    params = {'begin_date': start.strftime('%Y%m%d'), 'end_date': end.strftime('%Y%m%d'), 'station': station, 'product': 'water_level', 'datum': datum, 'time_zone': 'gmt', 'units': 'metric', 'format': 'json', 'application': 'research_toolkit'}
    r = release_runtime.run(['/usr/bin/curl', '--fail', '--silent', '--show-error', '--max-time', '30', BASE + '?' + urlencode(params)], capture_output=True, text=True, check=True)
    data = json.loads(r.stdout)
    if 'error' in data:
        raise ValueError('NOAA API: ' + str(data['error'].get('message', data['error'])))
    if data.get('metadata', {}).get('id') != station or not isinstance(data.get('data'), list):
        raise ValueError('unexpected NOAA response')
    return {'source': 'NOAA CO-OPS', 'product': 'observed six-minute water level', 'datum': datum, 'unit': 'metres', 'time_zone': 'GMT', 'begin_date': begin_date, 'end_date': end_date, 'metadata': data['metadata'], 'observations': data['data'], 'note': 'Water level is relative to the requested local station datum; quality flag q and NOAA notices must be considered. Datum availability varies by station.'}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('station')
    p.add_argument('begin_date')
    p.add_argument('end_date')
    p.add_argument('--datum', default='MLLW')
    a = p.parse_args()
    print(json.dumps(water_level(a.station, a.begin_date, a.end_date, a.datum), ensure_ascii=False, indent=2))
if __name__ == '__main__':
    main()
