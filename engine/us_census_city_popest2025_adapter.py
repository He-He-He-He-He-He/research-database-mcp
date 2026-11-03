"""US Census Vintage 2025 population estimates for cities and towns."""
import release_runtime
import argparse, csv, io, json, re, requests
BASE = 'https://www2.census.gov/programs-surveys/popest/datasets/2020-2025/cities/totals/'
LEVELS = ('040', '050', '061', '071', '157', '162', '170', '172')

def query(state_fips, year=2025, name='', sumlev='162', limit=100, offset=0):
    if not isinstance(state_fips, str) or not re.fullmatch('\\d{2}', state_fips) or type(year) is not int or (year not in range(2020, 2026)) or (not isinstance(name, str)) or (len(name) > 100) or (sumlev not in LEVELS) or (type(limit) is not int) or (not 1 <= limit <= 1000) or (type(offset) is not int) or (not 0 <= offset <= 1000000):
        raise ValueError('invalid query')
    url = BASE + 'sub-est2025_' + str(int(state_fips)) + '.csv'
    r = requests.get(url, timeout=50)
    r.raise_for_status()
    if len(r.content) > 5000000:
        raise ValueError('unexpected file size')
    rows = csv.DictReader(io.StringIO(r.content.decode('latin1')))
    if not {'SUMLEV', 'STATE', 'NAME', 'PLACE', 'POPESTIMATE2025'}.issubset(rows.fieldnames or []):
        raise ValueError('unexpected schema')
    out = []
    for x in rows:
        if x['STATE'] != state_fips or x['SUMLEV'] != sumlev or (name and name.casefold() not in x['NAME'].casefold()):
            continue
        keys = ['SUMLEV', 'STATE', 'COUNTY', 'PLACE', 'COUSUB', 'CONCIT', 'PRIMGEO_FLAG', 'FUNCSTAT', 'NAME', 'STNAME', 'POPESTIMATE' + str(year)]
        out.append({k: x[k] for k in keys})
    selected = out[offset:offset + limit]
    return {'source': url, 'vintage': 2025, 'estimate_date': f'{year}-07-01', 'matched_count': len(out), 'offset': offset, 'limit': limit, 'next_offset': offset + len(selected) if offset + len(selected) < len(out) else None, 'truncated': offset + len(selected) < len(out), 'records': selected, 'note': 'Local slice in source order; each request refetches the CSV and revisions may change values or ordering. SUMLEV and FUNCSTAT distinguish geographic and functional types; source values remain strings.'}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('state_fips')
    p.add_argument('--year', type=int, default=2025)
    p.add_argument('--name', default='')
    p.add_argument('--sumlev', choices=LEVELS, default='162')
    p.add_argument('--limit', type=int, default=100)
    p.add_argument('--offset', type=int, default=0)
    a = p.parse_args()
    print(json.dumps(query(a.state_fips, a.year, a.name, a.sumlev, a.limit, a.offset), ensure_ascii=False, indent=2))
if __name__ == '__main__':
    main()
