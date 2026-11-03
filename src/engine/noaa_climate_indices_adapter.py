"""NOAA PSL selected climate index series from official monthly text files."""
import release_runtime
import argparse, json, re
import requests
ROOT = 'https://www.psl.noaa.gov/data/correlation/'
CATALOG = {'oni': {'file': 'oni.data', 'name': 'Oceanic Niño Index', 'unit': 'degrees Celsius anomaly', 'period_note': 'Three-month running mean; month column represents the central month.'}, 'nina34': {'file': 'nina34.anom.data', 'name': 'Niño 3.4 SST anomaly', 'unit': 'degrees Celsius anomaly', 'period_note': 'Monthly SST anomaly; baseline 1981–2010 per source file.'}, 'nao': {'file': 'nao.data', 'name': 'North Atlantic Oscillation', 'unit': 'index', 'period_note': 'Monthly atmospheric index.'}, 'soi': {'file': 'soi.data', 'name': 'Southern Oscillation Index', 'unit': 'index', 'period_note': 'Monthly atmospheric index.'}}

def catalog():
    return {'source': 'https://psl.noaa.gov/data/climateindices/list/', 'series': CATALOG}

def observations(series, start, end, limit=120, *, offset=0):
    if series not in CATALOG or not 1800 <= start <= end <= 2100 or (not 1 <= limit <= 1000) or (type(offset) is not int) or (offset < 0):
        raise ValueError('invalid series, years, limit or offset')
    u = ROOT + CATALOG[series]['file']
    with requests.get(u, timeout=30, stream=True) as r:
        r.raise_for_status()
        chunks = []
        size = 0
        for b in r.iter_content(65536):
            size += len(b)
            if size > 1024 * 1024:
                raise ValueError('response exceeds 1 MiB')
            chunks.append(b)
    lines = b''.join(chunks).decode('utf-8').splitlines()
    bounds = lines[0].split()
    if len(bounds) != 2 or not all((x.isdigit() for x in bounds)):
        raise ValueError('unexpected source header')
    first, last = map(int, bounds)
    n = last - first + 1
    if n < 1 or n > 300 or len(lines) < n + 2:
        raise ValueError('unexpected source length')
    missing_raw = lines[n + 1].strip()
    missing = float(missing_raw)
    records = []
    missing_observations = []
    total = 0
    for line in lines[1:n + 1]:
        fields = line.split()
        if len(fields) != 13 or not re.fullmatch('\\d{4}', fields[0]):
            raise ValueError('unexpected source row')
        year = int(fields[0])
        if not start <= year <= end:
            continue
        for month, raw in enumerate(fields[1:], 1):
            value = float(raw)
            if value == missing:
                missing_observations.append({'year': year, 'month': month, 'raw_value': raw})
                continue
            if offset <= total < offset + limit:
                records.append({'year': year, 'month': month, 'value': value, 'raw_value': raw})
            total += 1
    return {'source': u, **CATALOG[series], 'missing_value': missing, 'missing_value_raw': missing_raw, 'missing_observations': missing_observations, 'total': total, 'offset': offset, 'returned': len(records), 'next_offset': offset + limit if offset + limit < total else None, 'truncated': offset + limit < total, 'observations': records, 'source_notes': lines[n + 2:], 'note': 'total counts nonmissing observations; missing_observations lists source missing markers separately. Each request refetches the source, and source updates can alter records or ordering.'}

def main():
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest='cmd', required=True)
    sub.add_parser('catalog')
    a = sub.add_parser('observations')
    a.add_argument('series')
    a.add_argument('--start', type=int, required=True)
    a.add_argument('--end', type=int, required=True)
    a.add_argument('--limit', type=int, default=120)
    a.add_argument('--offset', type=int, default=0)
    a = p.parse_args()
    result = catalog() if a.cmd == 'catalog' else observations(a.series, a.start, a.end, a.limit, offset=a.offset)
    print(json.dumps(result, ensure_ascii=False, indent=2))
if __name__ == '__main__':
    main()
