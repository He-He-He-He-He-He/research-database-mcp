"""WHO Mortality Database historical ICD-7, ICD-8 and ICD-9 records."""
import release_runtime
import argparse, csv, io, json, re, zipfile
from who_mortality_icd10_recent_adapter import _zip, BASE, INFO
REVISIONS = {7: ('morticd07.zip?sfvrsn=c1ebfbb2_3&ua=1', 'morticd7', ('07A', '07B'), 1950, 1972), 8: ('morticd08.zip?sfvrsn=6e1eba55_7&ua=1', 'morticd8', ('08A', '08B'), 1968, 2008), 9: ('morticd09.zip?sfvrsn=cfa97ceb_3&ua=1', 'morticd9', ('09A', '09B', '09C', '09N'), 1979, 2013)}

def query(revision, country, start, end, cause, icd_list, local_file=None, limit=100):
    if revision not in REVISIONS or not re.fullmatch('\\d{4}', country) or (not re.fullmatch('[A-Z0-9]{1,5}', cause)):
        raise ValueError('invalid revision, country or cause')
    filename, member, lists, lo, hi = REVISIONS[revision]
    if icd_list not in lists:
        raise ValueError('list does not belong to selected revision')
    if any((isinstance(x, bool) or not isinstance(x, int) for x in (start, end, limit))) or not lo <= start <= end <= hi or (not 1 <= limit <= 500):
        raise ValueError('invalid time range or limit')
    url = BASE + filename
    z = zipfile.ZipFile(local_file) if local_file else _zip(url)
    try:
        entries = z.infolist()
        if len(entries) != 1 or entries[0].file_size > 100000000 or entries[0].filename.lower() != member:
            raise ValueError('unexpected archive')
        with io.TextIOWrapper(z.open(entries[0]), encoding='utf-8-sig', newline='') as f:
            reader = csv.DictReader(f)
            if not {'Country', 'Admin1', 'SubDiv', 'Year', 'List', 'Cause', 'Sex', 'Deaths1'}.issubset(reader.fieldnames or []):
                raise ValueError('unexpected schema')
            out = []
            count = 0
            for row in reader:
                if row['Country'] != country or row['List'] != icd_list or row['Cause'] != cause or (not row['Year'].isdigit()) or (not start <= int(row['Year']) <= end):
                    continue
                count += 1
                if len(out) < limit:
                    out.append(row)
        return {'provider': None if local_file else 'World Health Organization Mortality Database', 'source': local_file if local_file else url, 'metadata': INFO, 'revision': revision, 'country_code': country, 'list': icd_list, 'cause': cause, 'matched_count': count, 'records': out, 'note': 'Deaths1 = registered deaths at all ages; Sex 1 male, 2 female, 9 unspecified. Admin1/SubDiv and age formats govern coverage. Not a mortality rate; death registration and diagnostic coding vary. Causes and ICD lists overlap and should not be summed or assumed directly comparable across revisions.' + (' Local archive provenance, version and coding conventions are unverified.' if local_file else '')}
    finally:
        z.close()

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('revision', type=int, choices=[7, 8, 9])
    p.add_argument('country')
    p.add_argument('start', type=int)
    p.add_argument('end', type=int)
    p.add_argument('cause')
    p.add_argument('icd_list')
    p.add_argument('--local-file')
    p.add_argument('--limit', type=int, default=100)
    a = p.parse_args()
    print(json.dumps(query(a.revision, a.country, a.start, a.end, a.cause, a.icd_list, a.local_file, a.limit), ensure_ascii=False, indent=2))
if __name__ == '__main__':
    main()
