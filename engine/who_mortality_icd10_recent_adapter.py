"""WHO Mortality Database ICD-10 part 6: recorded deaths 2021 onwards."""
import release_runtime
import argparse, csv, io, json, re, zipfile, requests
BASE = 'https://cdn.who.int/media/docs/default-source/world-health-data-platform/mortality-raw-data/'
URL = BASE + 'morticd10_part6.zip?sfvrsn=ec801a61_4'
COUNTRIES = BASE + 'mort_country_codes.zip?sfvrsn=800faac2_5&ua=1'
INFO = 'https://www.who.int/data/data-collection-tools/who-mortality-database'

def _zip(url, maxbytes=15000000):
    with requests.get(url, stream=True, timeout=60) as r:
        r.raise_for_status()
        b = bytearray()
        for c in r.iter_content(65536):
            b.extend(c)
            if len(b) > maxbytes:
                raise ValueError('download size exceeded')
    return zipfile.ZipFile(io.BytesIO(b))

def countries(keyword=''):
    with _zip(COUNTRIES, 100000) as z:
        with io.TextIOWrapper(z.open(z.namelist()[0]), encoding='utf-8-sig') as f:
            rows = list(csv.DictReader(f))
    return {'source': COUNTRIES, 'records': [r for r in rows if keyword.casefold() in (r['country'] + ' ' + r['name']).casefold()]}

def query(country, start, end, cause, icd_list, local_file=None, limit=100):
    if not re.fullmatch('\\d{4}', country) or not re.fullmatch('[A-Z0-9]{1,5}', cause) or icd_list not in ('101', '103', '104', '10M'):
        raise ValueError('invalid country, cause or ICD-10 list')
    if any((isinstance(x, bool) or not isinstance(x, int) for x in (start, end, limit))) or not 2021 <= start <= end <= 2030 or (not 1 <= limit <= 500):
        raise ValueError('invalid bounds')
    z = zipfile.ZipFile(local_file) if local_file else _zip(URL)
    try:
        files = z.infolist()
        if len(files) != 1 or files[0].file_size > 100000000:
            raise ValueError('unexpected archive contents')
        with io.TextIOWrapper(z.open(files[0]), encoding='utf-8-sig', newline='') as f:
            reader = csv.DictReader(f)
            if not {'Country', 'Admin1', 'SubDiv', 'Year', 'List', 'Cause', 'Sex', 'Deaths1'}.issubset(reader.fieldnames or []):
                raise ValueError('unexpected CSV schema')
            total = 0
            rows = []
            for r in reader:
                if r['Country'] != country or r['List'] != icd_list or r['Cause'] != cause or (not r['Year'].isdigit()) or (not start <= int(r['Year']) <= end):
                    continue
                total += 1
                if len(rows) < limit:
                    rows.append(r)
        return {'provider': None if local_file else 'World Health Organization Mortality Database', 'source': local_file if local_file else URL, 'metadata': INFO, 'file': None if local_file else 'ICD-10 part 6, 2021 onwards', 'country_code': country, 'list': icd_list, 'cause': cause, 'matched_count': total, 'records': rows, 'note': 'Deaths1 is registered deaths at all ages; sex 1 male, 2 female, 9 unspecified. Admin1/SubDiv and format codes affect coverage and age group interpretations. Counts, not rates; certification, completeness, coding and reporting years vary. ICD lists overlap; do not sum across lists or hierarchical causes.' + (' Local archive provenance, version and coding conventions are unverified.' if local_file else '')}
    finally:
        z.close()

def main():
    p = argparse.ArgumentParser(description=__doc__)
    s = p.add_subparsers(dest='action', required=True)
    a = s.add_parser('countries')
    a.add_argument('keyword', nargs='?', default='')
    a = s.add_parser('query')
    a.add_argument('country')
    a.add_argument('start', type=int)
    a.add_argument('end', type=int)
    a.add_argument('cause')
    a.add_argument('icd_list')
    a.add_argument('--local-file')
    a.add_argument('--limit', type=int, default=100)
    a = p.parse_args()
    v = countries(a.keyword) if a.action == 'countries' else query(a.country, a.start, a.end, a.cause, a.icd_list, a.local_file, a.limit)
    print(json.dumps(v, ensure_ascii=False, indent=2))
if __name__ == '__main__':
    main()
