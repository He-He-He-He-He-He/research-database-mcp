"""Read BIS central bank daily policy rate and unit metadata, read-only."""
import release_runtime
import argparse
import datetime
import json
import re
import subprocess
import threading
import time
import xml.etree.ElementTree as ET
from urllib.parse import urlencode
BASE = 'https://stats.bis.org/api/v1'
_lock = threading.Lock()
_last = 0.0

def _get(path):
    global _last
    with _lock:
        delay = 1 - (time.monotonic() - _last)
        if delay > 0:
            time.sleep(delay)
        _last = time.monotonic()
        r = release_runtime.run(['/usr/bin/curl', '--fail', '--silent', '--show-error', '--compressed', '--max-time', '25', '--write-out', '\n%{http_code}', BASE + path], capture_output=True, text=True, check=True)
    body, status = r.stdout.rsplit('\n', 1)
    if status == '204':
        return None
    return ET.fromstring(body)

def unit_metadata(unit='368'):
    if not isinstance(unit, str) or not re.fullmatch('[0-9]{1,5}', unit):
        raise ValueError('invalid unit code')
    root = _get('/codelist/BIS/CL_BIS_UNIT/1.0/' + unit)
    if root is None:
        raise ValueError('unit not found')
    codes = [x for x in root.iter() if x.tag.endswith('}Code') and x.get('id') == unit]
    if len(codes) != 1:
        raise ValueError('unexpected unit metadata')
    names = [x.text for x in codes[0] if x.tag.endswith('}Name') and x.get('{http://www.w3.org/XML/1998/namespace}lang') == 'en']
    if not names:
        raise ValueError('missing unit label')
    return {'code': unit, 'label': names[0]}

def policy_rate(area, date):
    if not isinstance(area, str) or not re.fullmatch('[A-Z]{2}', area):
        raise ValueError('area must be two uppercase letters')
    try:
        if not isinstance(date, str) or datetime.date.fromisoformat(date).isoformat() != date:
            raise ValueError
    except ValueError:
        raise ValueError('date must be YYYY-MM-DD') from None
    root = _get('/data/BIS,WS_CBPOL,1.0/D.' + area + '/all?' + urlencode({'startPeriod': date, 'endPeriod': date}))
    if root is None:
        return []
    sets = [x for x in root.iter() if x.tag.endswith('}DataSet')]
    output = []
    for ds in sets:
        for series in ds:
            if not series.tag.split('}')[-1] == 'Series':
                continue
            if series.get('REF_AREA') != area or series.get('FREQ') != 'D':
                raise ValueError('unexpected BIS series')
            for obs in series:
                if obs.tag.split('}')[-1] == 'Obs':
                    if obs.get('TIME_PERIOD') != date:
                        raise ValueError('unexpected date')
                    output.append({'dataset_attributes': dict(ds.attrib), 'series': dict(series.attrib), 'observation': dict(obs.attrib)})
    return output

def main():
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest='command', required=True)
    u = sub.add_parser('unit')
    u.add_argument('code', nargs='?', default='368')
    r = sub.add_parser('rate')
    r.add_argument('area')
    r.add_argument('date')
    a = p.parse_args()
    print(json.dumps(unit_metadata(a.code) if a.command == 'unit' else policy_rate(a.area, a.date), ensure_ascii=False, indent=2))
if __name__ == '__main__':
    main()
