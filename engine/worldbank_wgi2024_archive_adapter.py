"""World Bank Worldwide Governance Indicators 2024 historical update workbook."""
import release_runtime
import argparse, hashlib, io, json, re
import openpyxl, requests
URL = 'https://www.worldbank.org/content/dam/sites/govindicators/doc/wgidataset-2024.xlsx'
PAGE = 'https://www.worldbank.org/en/publication/worldwide-governance-indicators/documentation/previous-dataset'
DIMENSIONS = {'cc': 'Control of Corruption', 'ge': 'Government Effectiveness', 'pv': 'Political Stability and Absence of Violence/Terrorism', 'rl': 'Rule of Law', 'rq': 'Regulatory Quality', 'va': 'Voice and Accountability'}

def query(country, indicator='', start=2020, end=2023):
    if not isinstance(country, str) or not re.fullmatch('[A-Z0-9]{3}', country) or indicator not in ('', *DIMENSIONS):
        raise ValueError('invalid country or indicator')
    if any((type(x) is not int for x in (start, end))) or not 1996 <= start <= end <= 2023:
        raise ValueError('invalid year range')
    with requests.get(URL, stream=True, timeout=40) as r:
        r.raise_for_status()
        modified = r.headers.get('Last-Modified')
        raw = r.raw.read(6000001, decode_content=True)
    if len(raw) > 6000000:
        raise ValueError('workbook too large')
    w = openpyxl.load_workbook(io.BytesIO(raw), read_only=True, data_only=True)
    try:
        rows = w['Sheet1'].values
        headers = next(rows)
        expected = ('codeindyr', 'code', 'countryname', 'year', 'indicator', 'estimate', 'stddev', 'nsource', 'pctrank', 'pctranklower', 'pctrankupper')
        if tuple(headers) != expected:
            raise ValueError('unexpected workbook schema')
        out = []
        for row in rows:
            if row[1] == country and type(row[3]) is int and (start <= row[3] <= end) and (not indicator or row[4] == indicator):
                out.append(dict(zip(headers, row)))
        return {'source': URL, 'archive_page': PAGE, 'edition': '2024 update', 'workbook_modified': str(w.properties.modified), 'http_last_modified': modified, 'source_sha256': hashlib.sha256(raw).hexdigest(), 'indicator_labels': DIMENSIONS, 'matched_count': len(out), 'records': out, 'note': 'World Bank WGI research indicators combine perceptions, not direct objective governance measurements. Preserve standardized estimates, standard errors, source counts and percentile-rank uncertainty bounds; cross-country and over-time differences may be statistically uncertain and source composition changes. 2024 edition is not the same as a 2024 observation (this file runs through 2023). The workbook internal modified timestamp is 2024-09-27 while server Last-Modified observed 2025-11-19; exact file availability before July 2025 is not independently established. Missing rows do not mean zero. Consult original methodology and use/licence restrictions.'}
    finally:
        w.close()

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('country')
    p.add_argument('--indicator', choices=list(DIMENSIONS), default='')
    p.add_argument('--start', type=int, default=2020)
    p.add_argument('--end', type=int, default=2023)
    a = p.parse_args()
    print(json.dumps(query(a.country, a.indicator, a.start, a.end), ensure_ascii=False, indent=2))
if __name__ == '__main__':
    main()
