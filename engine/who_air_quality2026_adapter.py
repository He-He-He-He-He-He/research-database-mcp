"""WHO Ambient Air Quality Database v8.0 (June 2026), city-year records."""
import release_runtime
import argparse, csv, io, json, re, requests, openpyxl
URL = 'https://cdn.who.int/media/docs/default-source/air-pollution-documents/air-quality-and-health/who-ambient-air-quality-database-version-2026-v8.xlsx?sfvrsn=95d122a4_5&download=true'
SHEET = 'GlobalCity_Db_V8.0_2026-06-28'

def observations(country, city=None, year=None, limit=100):
    if not re.fullmatch('[A-Z]{3}', country):
        raise ValueError('country must be ISO3')
    if city is not None and (not isinstance(city, str) or len(city) > 120):
        raise ValueError('invalid city filter')
    if year is not None and (isinstance(year, bool) or not isinstance(year, int) or (not 1900 <= year <= 2100)):
        raise ValueError('invalid year')
    if not 1 <= limit <= 1000:
        raise ValueError('invalid limit')
    with requests.get(URL, timeout=60, stream=True) as r:
        r.raise_for_status()
        parts = []
        n = 0
        for part in r.iter_content(65536):
            n += len(part)
            if n > 10000000:
                raise ValueError('file exceeds 10 MB')
            parts.append(part)
    w = openpyxl.load_workbook(io.BytesIO(b''.join(parts)), read_only=True, data_only=True)
    try:
        s = w[SHEET]
        rows = s.iter_rows(values_only=True)
        head = next(csv.reader([next(rows)[0]], strict=True))
        if not {'iso3', 'city', 'year', 'pm25_concentration', 'reference'}.issubset(head):
            raise ValueError('unexpected header')
        out = []
        count = 0
        malformed = 0
        for cells in rows:
            line = ','.join((str(v) for v in cells if v is not None))
            if not line:
                continue
            try:
                vals = next(csv.reader([line], strict=True))
            except csv.Error:
                malformed += 1
                continue
            if len(vals) != len(head):
                malformed += 1
                continue
            x = dict(zip(head, vals))
            if x['iso3'] != country or (city and city.casefold() not in {x['city'].casefold(), x['city'].split('/')[0].casefold()}) or (year is not None and x['year'] != str(year)):
                continue
            count += 1
            if len(out) < limit:
                out.append(x)
        return {'provider': 'World Health Organization', 'dataset': 'Ambient Air Quality Database v8.0', 'source': URL, 'matched_count': count, 'returned_count': len(out), 'malformed_rows_skipped': malformed, 'records': out, 'note': 'Annual average concentration in µg/m³, source text and temporal coverage retained; NA is missing, not zero. Do not rank cities without comparability assessment.'}
    finally:
        w.close()

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('country')
    p.add_argument('--city')
    p.add_argument('--year', type=int)
    p.add_argument('--limit', type=int, default=100)
    a = p.parse_args()
    print(json.dumps(observations(a.country, a.city, a.year, a.limit), ensure_ascii=False, indent=2))
if __name__ == '__main__':
    main()
