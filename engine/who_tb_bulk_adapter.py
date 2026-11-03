"""WHO TB data: bounded retrieval and local country/year/variable filtering."""
import release_runtime
import argparse
import csv
import io
import json
import re
import requests
BASE = 'https://extranet.who.int/tme/generateCSV.asp'
DATASETS = {'dictionary', 'estimates', 'estimates_age_sex', 'mdr_rr_estimates', 'ltbi_estimates', 'budget', 'notifications', 'community', 'dr_surveillance', 'expenditure_utilisation', 'labs', 'tbhivnonroutinesurv', 'policies', 'ppm', 'contact_tpt', 'outcomes', 'outcomes_age_sex', 'unhlm', 'zoonotic', 'provisional_notifications'}
MAX_BYTES = 20000000

def query(dataset, iso3=None, year=None, columns=None, keyword=None, limit=100):
    if dataset not in DATASETS:
        raise ValueError('Unknown WHO dataset')
    if not 1 <= limit <= 1000:
        raise ValueError('limit must be 1..1000')
    if dataset != 'dictionary' and (not isinstance(iso3, str) or not re.fullmatch('[A-Z]{3}', iso3)):
        raise ValueError('country ISO3 is required for data queries')
    if year is not None and (isinstance(year, bool) or not 1900 <= int(year) <= 2100):
        raise ValueError('invalid year')
    with requests.get(BASE, params={'ds': dataset}, timeout=60, stream=True) as r:
        r.raise_for_status()
        url = r.url
        chunks = []
        size = 0
        for chunk in r.iter_content(65536):
            size += len(chunk)
            if size > MAX_BYTES:
                raise ValueError('WHO CSV exceeds 20 MB limit')
            chunks.append(chunk)
    text = b''.join(chunks).decode('utf-8-sig')
    reader = csv.DictReader(io.StringIO(text))
    if not reader.fieldnames or ('variable_name' if dataset == 'dictionary' else 'iso3') not in reader.fieldnames:
        raise ValueError('Unexpected CSV format or unsupported dataset layout')
    cols = columns.split(',') if columns else None
    if cols and any((c not in reader.fieldnames for c in cols)):
        raise ValueError('Unknown column; consult dictionary and headers')
    count = 0
    out = []
    for row in reader:
        if iso3 and row.get('iso3', '').upper() != iso3:
            continue
        if year is not None and row.get('year') != str(year):
            continue
        if keyword and keyword.casefold() not in json.dumps(row, ensure_ascii=False).casefold():
            continue
        count += 1
        if len(out) < limit:
            out.append({k: row[k] for k in cols} if cols else row)
    return {'provider': 'World Health Organization Global TB Programme', 'dataset': dataset, 'source': url, 'headers': reader.fieldnames, 'matched_count': count, 'returned_count': len(out), 'records': out, 'note': 'Values are source strings; empty is missing, not zero. Consult WHO dictionary and distinguish estimates from reported notifications.'}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('dataset', choices=sorted(DATASETS))
    p.add_argument('--iso3')
    p.add_argument('--year', type=int)
    p.add_argument('--columns')
    p.add_argument('--keyword')
    p.add_argument('--limit', type=int, default=100)
    a = p.parse_args()
    print(json.dumps(query(a.dataset, a.iso3, a.year, a.columns, a.keyword, a.limit), ensure_ascii=False, indent=2))
if __name__ == '__main__':
    main()
