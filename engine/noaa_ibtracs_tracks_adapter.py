"""Read NOAA IBTrACS v04r01 best-track CSV with bounded local filtering."""
import release_runtime
import argparse
import csv
import json
import re
import requests
BASE = 'https://www.ncei.noaa.gov/data/international-best-track-archive-for-climate-stewardship-ibtracs/v04r01/access/csv/'
SUBSETS = {'last3years', 'ACTIVE', 'WP', 'EP', 'NA', 'NI', 'SI', 'SP', 'SA', 'since1980'}
MAX_BYTES = 160000000

def tracks(subset='last3years', season=None, name=None, sid=None, basin=None, limit=100):
    if subset not in SUBSETS:
        raise ValueError('unsupported subset')
    if season is None and (not sid) and (not name):
        raise ValueError('provide season, name, or SID to filter')
    if season is not None and (isinstance(season, bool) or not 1800 <= int(season) <= 2100):
        raise ValueError('invalid season')
    if not 1 <= limit <= 1000:
        raise ValueError('limit must be 1..1000')
    for v in (name, sid, basin):
        if v is not None and (not isinstance(v, str) or len(v) > 60 or (not re.fullmatch('[A-Za-z0-9 _-]+', v))):
            raise ValueError('invalid text filter')
    url = BASE + f'ibtracs.{subset}.list.v04r01.csv'
    with requests.get(url, timeout=120, stream=True) as r:
        r.raise_for_status()
        r.encoding = 'utf-8'
        n = 0

        def lines():
            nonlocal n
            for line in r.iter_lines(decode_unicode=True):
                n += len(line) + 1
                if n > MAX_BYTES:
                    raise ValueError('Response exceeds 160 MB')
                yield line
        reader = csv.reader(lines())
        headers = next(reader)
        units = next(reader)
        if not {'SID', 'SEASON', 'BASIN', 'NAME', 'ISO_TIME', 'LAT', 'LON'}.issubset(headers):
            raise ValueError('Unexpected IBTrACS columns')
        matched = 0
        out = []
        for fields in reader:
            if len(fields) != len(headers):
                raise ValueError('Unexpected IBTrACS row width')
            row = dict(zip(headers, (x.strip() for x in fields)))
            if season is not None and row['SEASON'] != str(season):
                continue
            if sid and row['SID'].upper() != sid.upper():
                continue
            if name and row['NAME'].upper() != name.upper():
                continue
            if basin and row['BASIN'].upper() != basin.upper():
                continue
            matched += 1
            if len(out) < limit:
                out.append(row)
    return {'source': url, 'provider': 'NOAA NCEI IBTrACS', 'units': dict(zip(headers, (x.strip() for x in units))), 'matched_count': matched, 'returned_count': len(out), 'records': out, 'note': 'Historical best-track observations, not a live warning. Wind data agencies can use different averaging periods.'}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--subset', choices=sorted(SUBSETS), default='last3years')
    p.add_argument('--season', type=int)
    p.add_argument('--name')
    p.add_argument('--sid')
    p.add_argument('--basin')
    p.add_argument('--limit', type=int, default=100)
    a = p.parse_args()
    print(json.dumps(tracks(a.subset, a.season, a.name, a.sid, a.basin, a.limit), ensure_ascii=False, indent=2))
if __name__ == '__main__':
    main()
