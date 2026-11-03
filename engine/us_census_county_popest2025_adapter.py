"""US Census Vintage 2025 state and county population estimates and components."""
import release_runtime
import argparse, csv, io, json, requests
URL = 'https://www2.census.gov/programs-surveys/popest/datasets/2020-2025/counties/totals/co-est2025-alldata.csv'

def query(state='', county='', level='county', year=2025, limit=100, offset=0):
    if level not in ('county', 'state') or type(year) is not int or year not in range(2020, 2026) or (not isinstance(state, str)) or (not isinstance(county, str)) or (len(state) > 80) or (len(county) > 80) or (type(limit) is not int) or (not 1 <= limit <= 1000) or (type(offset) is not int) or (not 0 <= offset <= 1000000):
        raise ValueError('invalid query')
    r = requests.get(URL, timeout=60)
    r.raise_for_status()
    if len(r.content) > 5000000:
        raise ValueError('unexpected file size')
    rows = csv.DictReader(io.StringIO(r.content.decode('latin1')))
    if not {'SUMLEV', 'STATE', 'COUNTY', 'STNAME', 'CTYNAME', 'POPESTIMATE2025'}.issubset(rows.fieldnames or []):
        raise ValueError('unexpected schema')
    out = []
    for row in rows:
        if row['SUMLEV'] != ('050' if level == 'county' else '040'):
            continue
        if state and state.casefold() not in (row['STNAME'].casefold(), row['STATE']):
            continue
        if county and county.casefold() not in (row['CTYNAME'].casefold(), row['COUNTY']):
            continue
        keys = ['SUMLEV', 'STATE', 'COUNTY', 'STNAME', 'CTYNAME'] + [x for x in row if x.endswith(str(year))]
        out.append({k: row[k] for k in keys})
    selected = out[offset:offset + limit]
    return {'source': URL, 'vintage': 2025, 'year': year, 'matched_count': len(out), 'offset': offset, 'limit': limit, 'returned': len(selected), 'next_offset': offset + len(selected) if offset + len(selected) < len(out) else None, 'truncated': offset + len(selected) < len(out), 'records': selected, 'note': 'Local slice in source order; each request refetches the source CSV, which may be revised or reordered. County and state records are distinct levels; estimates and annual components retain source strings and definitions.'}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--state', default='')
    p.add_argument('--county', default='')
    p.add_argument('--level', choices=['county', 'state'], default='county')
    p.add_argument('--year', type=int, default=2025)
    p.add_argument('--limit', type=int, default=100)
    p.add_argument('--offset', type=int, default=0)
    a = p.parse_args()
    print(json.dumps(query(a.state, a.county, a.level, a.year, a.limit, a.offset), ensure_ascii=False, indent=2))
if __name__ == '__main__':
    main()
