"""WHO Mortality Database ICD-10 historical parts 1–4, through 2016."""
import release_runtime
import argparse, csv, io, json, re, zipfile
from who_mortality_icd10_recent_adapter import _zip, BASE, INFO
PARTS = {1: ('morticd10_part1.zip?sfvrsn=e2a4f93a_19&ua=1', 1950, 2002), 2: ('morticd10_part2.zip?sfvrsn=6e55000b_6&ua=1', 2003, 2007), 3: ('morticd10_part3.zip?sfvrsn=9f1111a2_14&ua=1', 2008, 2012), 4: ('morticd10_part4.zip?sfvrsn=259c5c23_30&ua=1', 2013, 2016)}

def query(part, country, start, end, cause, icd_list, local_file=None, limit=100):
    if part not in PARTS or not re.fullmatch('\\d{4}', country) or (not re.fullmatch('[A-Z0-9]{1,5}', cause)) or (icd_list not in ('101', '103', '104', '10M')):
        raise ValueError('invalid part, country, cause or ICD list')
    filename, lo, hi = PARTS[part]
    if any((isinstance(x, bool) or not isinstance(x, int) for x in (start, end, limit))) or not lo <= start <= end <= hi or (not 1 <= limit <= 500):
        raise ValueError('years must be within chosen part, limit 1–500')
    url = BASE + filename
    z = zipfile.ZipFile(local_file) if local_file else _zip(url)
    try:
        files = z.infolist()
        if len(files) != 1 or files[0].file_size > 100000000 or files[0].filename.lower() != f'morticd10_part{part}':
            raise ValueError('wrong or oversized archive')
        with io.TextIOWrapper(z.open(files[0]), encoding='utf-8-sig', newline='') as f:
            reader = csv.DictReader(f)
            if not {'Country', 'Admin1', 'SubDiv', 'Year', 'List', 'Cause', 'Sex', 'Deaths1'}.issubset(reader.fieldnames or []):
                raise ValueError('unexpected schema')
            count = 0
            rows = []
            for r in reader:
                if r['Country'] != country or r['List'] != icd_list or r['Cause'] != cause or (not r['Year'].isdigit()) or (not start <= int(r['Year']) <= end):
                    continue
                count += 1
                if len(rows) < limit:
                    rows.append(r)
        return {'provider': None if local_file else 'World Health Organization Mortality Database', 'source': local_file if local_file else url, 'metadata': INFO, 'part': part, 'country_code': country, 'list': icd_list, 'cause': cause, 'matched_count': count, 'records': rows, 'note': 'Deaths1 is registered deaths at all ages; sex 1 male, 2 female, 9 unspecified. Admin1/SubDiv and age format codes affect coverage and interpretation. Counts, not rates. ICD lists and hierarchical causes overlap; do not sum them. Coverage, coding and reporting vary.' + (' Local archive provenance, version and coding conventions are unverified.' if local_file else '')}
    finally:
        z.close()

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('part', type=int, choices=[1, 2, 3, 4])
    p.add_argument('country')
    p.add_argument('start', type=int)
    p.add_argument('end', type=int)
    p.add_argument('cause')
    p.add_argument('icd_list')
    p.add_argument('--local-file')
    p.add_argument('--limit', type=int, default=100)
    a = p.parse_args()
    print(json.dumps(query(a.part, a.country, a.start, a.end, a.cause, a.icd_list, a.local_file, a.limit), ensure_ascii=False, indent=2))
if __name__ == '__main__':
    main()
