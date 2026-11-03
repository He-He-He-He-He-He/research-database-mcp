"""World Bank PIP September 2026 poverty estimates and projection scenarios."""
import release_runtime
import argparse, csv, io, json, re, requests
BASE = 'https://datacatalogfiles.worldbank.org/ddh-published/0067066/'
FILES = {'country': 'DR0096368/Country_FGT_1981_2050_20260922_2021_01_02_PROD.csv', 'global': 'DR0096369/Global_FGT_1981_2050_20260922_2021_01_02_PROD.csv', 'country_scenario': 'DR0096367/Country_FGT_VariousScenarios_2027_2050_20260922_2021_01_02_PROD.csv', 'global_scenario': 'DR0096370/Global_FGT_VariousScenarios_2027_2050_20260922_2021_01_02_PROD.csv'}

def query(kind, country='', start=2025, end=2030, povertyline='', scenario='', limit=100, *, offset=0):
    if kind not in FILES or not isinstance(country, str) or (country and (not re.fullmatch('[A-Z]{3}', country))) or any((isinstance(v, bool) or not isinstance(v, int) for v in (start, end, limit))) or (not 1981 <= start <= end <= 2050) or (povertyline not in ('', '3', '4.2', '8.3')) or (not isinstance(scenario, str)) or (len(scenario) > 100) or (not 1 <= limit <= 1000) or (type(offset) is not int) or (offset < 0):
        raise ValueError('invalid query')
    if kind.startswith('global') and country:
        raise ValueError('global files have no country filter')
    if 'scenario' not in kind and scenario:
        raise ValueError('scenario filter requires a scenario file')
    url = BASE + FILES[kind]
    r = requests.get(url, timeout=90)
    r.raise_for_status()
    if len(r.content) > 15000000:
        raise ValueError('unexpected file size')
    rows = csv.DictReader(io.StringIO(r.content.decode('utf-8-sig')))
    if not {'year', 'povertyline', 'fgt0', 'fgt1', 'fgt2', 'pop'}.issubset(rows.fieldnames or []):
        raise ValueError('unexpected schema')
    data = []
    count = 0
    for x in rows:
        if not start <= int(x['year']) <= end or (country and x.get('code') != country) or (povertyline and x['povertyline'] != povertyline) or (scenario and x.get('scenario', '').casefold() != scenario.casefold()):
            continue
        if offset <= count < offset + limit:
            data.append(x)
        count += 1
    return {'source': url, 'vintage': 'September 2026', 'matched_count': count, 'offset': offset, 'returned': len(data), 'next_offset': offset + limit if offset + limit < count else None, 'truncated': offset + limit < count, 'records': data, 'note': 'Poverty-line values 3, 4.2 and 8.3 are daily international-dollar thresholds at 2021 PPP, not nominal local-currency amounts. Preserve estimate_type where supplied; do not infer observed versus projected from year alone. Future scenarios are conditional projections; fgt values are percentages and population is millions. Each request refetches the source file; updates may change ordering.'}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('kind', choices=FILES)
    p.add_argument('--country', default='')
    p.add_argument('--start', type=int, default=2025)
    p.add_argument('--end', type=int, default=2030)
    p.add_argument('--povertyline', choices=['3', '4.2', '8.3'], default='')
    p.add_argument('--scenario', default='')
    p.add_argument('--limit', type=int, default=100)
    p.add_argument('--offset', type=int, default=0)
    a = p.parse_args()
    print(json.dumps(query(a.kind, a.country, a.start, a.end, a.povertyline, a.scenario, a.limit, offset=a.offset), ensure_ascii=False, indent=2))
if __name__ == '__main__':
    main()
