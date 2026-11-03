"""World Bank Worldwide Governance Indicators 2023 update historical workbook."""
import release_runtime
import argparse, hashlib, io, json, re
import openpyxl, requests
URL = 'https://www.worldbank.org/content/dam/sites/govindicators/doc/wgidataset_2023.xlsx'
PAGE = 'https://www.worldbank.org/en/publication/worldwide-governance-indicators/documentation/previous-dataset'
SHEETS = {'cc': 'ControlofCorruption', 'ge': 'GovernmentEffectiveness', 'pv': 'Political StabilityNoViolence', 'rl': 'RuleofLaw', 'rq': 'RegulatoryQuality', 'va': 'VoiceandAccountability'}

def query(country, indicator='', start=2020, end=2022):
    if not isinstance(country, str) or not re.fullmatch('[A-Z0-9]{3}', country) or indicator not in ('', *SHEETS):
        raise ValueError('invalid country or indicator')
    if any((type(x) is not int for x in (start, end))) or not 1996 <= start <= end <= 2022:
        raise ValueError('invalid year range')
    with requests.get(URL, stream=True, timeout=40) as r:
        r.raise_for_status()
        modified = r.headers.get('Last-Modified')
        raw = r.raw.read(5000001, decode_content=True)
    if len(raw) > 5000000:
        raise ValueError('workbook too large')
    w = openpyxl.load_workbook(io.BytesIO(raw), read_only=True, data_only=True)
    try:
        out = []
        for code, name in SHEETS.items():
            if indicator and code != indicator:
                continue
            s = w[name]
            it = s.iter_rows(values_only=True)
            first = next(it)
            description = next(it)
            legend = []
            for i in range(3, 14):
                row = next(it)
                if i >= 4 and row[0] is not None:
                    legend.append([row[0], row[1]])
            years = next(it)
            metrics = next(it)
            if metrics[0] != 'Country/Territory' or metrics[1] != 'Code':
                raise ValueError('unexpected headers')
            for row in it:
                if row[1] != country:
                    continue
                grouped = {}
                for i in range(2, len(years)):
                    y = years[i]
                    m = metrics[i]
                    if type(y) is int and start <= y <= end and isinstance(m, str):
                        grouped.setdefault(y, {})[m] = row[i]
                for y, data in grouped.items():
                    out.append({'country': row[0], 'code': country, 'indicator': code, 'indicator_title': first[0], 'year': y, 'source_values': data})
                break
        return {'source': URL, 'archive_page': PAGE, 'edition': '2023 update', 'workbook_modified': str(w.properties.modified), 'http_last_modified': modified, 'source_sha256': hashlib.sha256(raw).hexdigest(), 'matched_count': len(out), 'records': out, 'legend': legend, 'note': 'World Bank WGI research indicators aggregate governance perceptions, not direct objective facts. 2023 update has data through 2022; source columns contain estimates, standard errors, source counts and 90% percentile rank bounds. Missing #N/A values are retained. Historical estimates may change across editions. Workbook internal modification was 2023-09-13, server Last-Modified observed 2024-10-16; these dates do not independently prove immutable prior availability. Check methodology and source terms.'}
    finally:
        w.close()

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('country')
    p.add_argument('--indicator', choices=list(SHEETS), default='')
    p.add_argument('--start', type=int, default=2020)
    p.add_argument('--end', type=int, default=2022)
    a = p.parse_args()
    print(json.dumps(query(a.country, a.indicator, a.start, a.end), ensure_ascii=False, indent=2))
if __name__ == '__main__':
    main()
