"""US Census county population by age, sex, race and Hispanic origin, Vintage 2025."""
import release_runtime
import argparse, csv, io, json, re, requests
BASE = 'https://www2.census.gov/programs-surveys/popest/datasets/2020-2025/counties/asrh/'

def query(state_fips, year=2025, county='', age_group=0, limit=100, offset=0):
    if not isinstance(state_fips, str) or not re.fullmatch('\\d{2}', state_fips) or type(year) is not int or (year not in range(2020, 2026)) or (not isinstance(county, str)) or (len(county) > 100) or (type(age_group) is not int) or (age_group not in range(19)) or (type(limit) is not int) or (not 1 <= limit <= 1000) or (type(offset) is not int) or (not 0 <= offset <= 1000000):
        raise ValueError('invalid argument')
    url = BASE + 'cc-est2025-alldata-' + state_fips + '.csv'
    r = requests.get(url, timeout=60)
    r.raise_for_status()
    if len(r.content) > 20000000:
        raise ValueError('unexpected file size')
    rows = csv.DictReader(io.StringIO(r.content.decode('latin1')))
    if not {'STATE', 'COUNTY', 'CTYNAME', 'YEAR', 'AGEGRP', 'TOT_POP', 'H_MALE'}.issubset(rows.fieldnames or []):
        raise ValueError('unexpected schema')
    data = [x for x in rows if x['YEAR'] == str(year - 2018) and x['AGEGRP'] == str(age_group) and (x['STATE'] == state_fips) and (not county or county.casefold() in (x['COUNTY'], x['CTYNAME'].casefold()))]
    selected = data[offset:offset + limit]
    return {'source': url, 'vintage': 2025, 'estimate_date': f'{year}-07-01', 'matched_count': len(data), 'offset': offset, 'limit': limit, 'next_offset': offset + len(selected) if offset + len(selected) < len(data) else None, 'truncated': offset + len(selected) < len(data), 'records': selected, 'note': 'Local slice in source order; each request refetches the source CSV and revisions may change values or ordering. County race, Hispanic origin, sex and age-group estimates retain raw strings and source definitions.'}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('state_fips')
    p.add_argument('--year', type=int, default=2025)
    p.add_argument('--county', default='')
    p.add_argument('--age-group', type=int, default=0)
    p.add_argument('--limit', type=int, default=100)
    p.add_argument('--offset', type=int, default=0)
    a = p.parse_args()
    print(json.dumps(query(a.state_fips, a.year, a.county, a.age_group, a.limit, a.offset), ensure_ascii=False, indent=2))
if __name__ == '__main__':
    main()
