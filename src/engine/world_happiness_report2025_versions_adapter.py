"""World Happiness Report 2025 original and revised Figure 2.1 files."""
import release_runtime
import io, hashlib, argparse, json
import requests, openpyxl
BASE = 'https://files.worldhappiness.report/WHR25_Data_Figure_2.1'
PAGE = 'https://www.worldhappiness.report/ed/2025/'

def query(country, version='original', start=2024, end=2024):
    if not isinstance(country, str) or not country.strip() or len(country) > 100:
        raise ValueError('invalid country')
    if version not in ('original', 'v2', 'v3'):
        raise ValueError('invalid version')
    if any((type(v) is not int for v in (start, end))) or not 2011 <= start <= end <= 2024:
        raise ValueError('invalid end-year range')
    url = BASE + ('' if version == 'original' else version) + '.xlsx'
    with requests.get(url, stream=True, timeout=40) as r:
        r.raise_for_status()
        modified = r.headers.get('Last-Modified')
        raw = r.raw.read(2000001, decode_content=True)
    if len(raw) > 2000000:
        raise ValueError('workbook exceeds limit')
    w = openpyxl.load_workbook(io.BytesIO(raw), read_only=True, data_only=True)
    try:
        rows = iter(w['Data for Figure 2.1 (2011–2024)'].values)
        header = next(rows)
        required = {'Year', 'Rank', 'Country name'}
        if not required.issubset(header):
            raise ValueError('unexpected columns')
        out = []
        for row in rows:
            d = dict(zip(header, row))
            year = d['Year']
            name = d['Country name']
            if isinstance(name, str) and name.casefold() == country.strip().casefold() and isinstance(year, (int, float)) and (start <= year <= end):
                out.append({k: d[k] for k in header if k is not None})
        return {'source': url, 'source_page': PAGE, 'report_publication_date': '2025-03-20', 'version': version, 'http_last_modified': modified, 'source_sha256': hashlib.sha256(raw).hexdigest(), 'records': out, 'note': 'Oxford Wellbeing Research Centre / Gallup / SDSN research report, not official UN statistics. Year is the ending year of a three-year survey average; ladder scale 0–10. Original and revised files use different whisker column names and order; original headers and values are retained. v2/v3 HTTP dates observed October 2025 and must not be treated as available before July 2025. Server Last-Modified is not independent historical archive proof. Observational explanatory decompositions do not establish causality.'}
    finally:
        w.close()

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('country')
    p.add_argument('--version', choices=['original', 'v2', 'v3'], default='original')
    p.add_argument('--start', type=int, default=2024)
    p.add_argument('--end', type=int, default=2024)
    a = p.parse_args()
    print(json.dumps(query(a.country, a.version, a.start, a.end), ensure_ascii=False, indent=2))
if __name__ == '__main__':
    main()
