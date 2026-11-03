"""IMF October 2026 WEO complete workbook: filter country and indicator."""
import release_runtime
import argparse, datetime, io, json, re, requests, openpyxl
URL = 'https://data.imf.org/-/media/iData/External-Storage/Documents/0FA3DC49A04D446E9D69DBEB29979E1C/en/WEOOct2026all.xlsx'

def query(country='', indicator='', start=2020, end=2031, limit=20, local_file=None):
    if not isinstance(country, str) or not isinstance(indicator, str) or len(country) > 100 or (len(indicator) > 100) or any((isinstance(v, bool) or not isinstance(v, int) for v in (start, end, limit))) or (not 1980 <= start <= end <= 2100) or (not 1 <= limit <= 200):
        raise ValueError('invalid query')
    if local_file:
        w = openpyxl.load_workbook(local_file, read_only=True, data_only=True)
    else:
        r = requests.get(URL, timeout=90)
        r.raise_for_status()
        if len(r.content) > 15000000:
            raise ValueError('unexpected file size')
        w = openpyxl.load_workbook(io.BytesIO(r.content), read_only=True, data_only=True)
    try:
        it = w['Countries'].iter_rows(values_only=True)
        headers = next(it)
        required = {'COUNTRY.ID', 'COUNTRY', 'INDICATOR.ID', 'INDICATOR', 'LATEST_ACTUAL_ANNUAL_DATA', 'UNIT', 'SCALE'}
        if not required.issubset(headers):
            raise ValueError('unexpected workbook schema')
        result = []
        count = 0
        for row in it:
            d = dict(zip(headers, row))
            if country and country.casefold() not in (str(d['COUNTRY.ID']).casefold(), str(d['COUNTRY']).casefold()):
                continue
            if indicator and indicator.casefold() not in (str(d['INDICATOR.ID']).casefold(), str(d['INDICATOR']).casefold()):
                continue
            count += 1
            if len(result) >= limit:
                continue
            meta = {str(k): v.isoformat() if isinstance(v, (datetime.datetime, datetime.date)) else v for k, v in d.items() if isinstance(k, str)}
            vals = {str(k): v for k, v in d.items() if isinstance(k, int) and start <= k <= end}
            result.append({'metadata': meta, 'values': vals})
        return {'source': local_file if local_file else URL, 'workbook_vintage': None if local_file else 'October 2026', 'local_file': bool(local_file), 'matched_count': count, 'records': result, 'note': 'Country and indicator filters match complete codes or complete names (case-insensitive), not substrings; no match does not mean the data is absent. Use per-series latest actual field and fiscal-year conventions to distinguish estimates and projections; blank values are missing.' + (' Local workbook provenance and version are unverified.' if local_file else '')}
    finally:
        w.close()

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--country', default='')
    p.add_argument('--indicator', default='')
    p.add_argument('--start', type=int, default=2020)
    p.add_argument('--end', type=int, default=2031)
    p.add_argument('--limit', type=int, default=20)
    p.add_argument('--local-file')
    a = p.parse_args()
    print(json.dumps(query(a.country, a.indicator, a.start, a.end, a.limit, a.local_file), ensure_ascii=False, indent=2))
if __name__ == '__main__':
    main()
