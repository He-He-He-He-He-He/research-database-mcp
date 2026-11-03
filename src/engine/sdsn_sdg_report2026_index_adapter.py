"""SDSN Sustainable Development Report 2026 SDG Index and backdated scores."""
import release_runtime
import argparse, io, json, re, requests, openpyxl
URL = 'https://dashboards.sdgindex.org/static/downloads/database_2026.xlsx'
INFO = 'https://dashboards.sdgindex.org/downloads/'

def query(country, start, end, local_file=None):
    if not re.fullmatch('[A-Z]{3}', country):
        raise ValueError('country must be uppercase ISO3')
    if any((isinstance(x, bool) or not isinstance(x, int) for x in (start, end))) or not 2000 <= start <= end <= 2025:
        raise ValueError('backdated years must be 2000–2025')
    if local_file:
        w = openpyxl.load_workbook(local_file, read_only=True, data_only=True)
    else:
        with requests.get(URL, stream=True, timeout=60) as r:
            r.raise_for_status()
            b = bytearray()
            for chunk in r.iter_content(65536):
                b.extend(chunk)
                if len(b) > 16000000:
                    raise ValueError('unexpected workbook size')
        w = openpyxl.load_workbook(io.BytesIO(b), read_only=True, data_only=True)
    try:
        s = w['Backdated SDG Index']
        h = next(s.iter_rows(max_row=1, max_col=5, values_only=True))
        if tuple(h) != ('id', 'country', 'year', 'indexreg_', 'sdgi_s'):
            raise ValueError('unexpected historical schema')
        historic = []
        for r in s.iter_rows(min_row=2, max_col=5, values_only=True):
            if r[0] == country and isinstance(r[2], int) and (start <= r[2] <= end):
                historic.append({'country': r[1], 'year': r[2], 'region': r[3], 'score': r[4]})
        s = w['SDR2026 Data']
        h = next(s.iter_rows(max_row=1, max_col=8, values_only=True))
        if h[0] != 'Country Code ISO3' or h[2] != '2026 SDG Index Score':
            raise ValueError('unexpected current schema')
        current = [dict(zip(h, r)) for r in s.iter_rows(min_row=2, max_col=8, values_only=True) if r[0] == country]
        return {'publisher': None if local_file else 'Sustainable Development Solutions Network (independent research network)', 'source': local_file if local_file else URL, 'documentation': INFO, 'license': None if local_file else 'CC BY-NC-ND 4.0 as stated in workbook', 'country': country, 'unit': None if local_file else 'SDG Index score (0–100)', 'backdated': historic, 'report_2026': current, 'note': ('Local workbook provenance, license, units, edition and interpretation are unverified. The following applies only if its identity is confirmed. ' if local_file else '') + 'SDSN composite research index, not the UN official SDG indicator series. Historic scores were retroactively calculated for the 2026 edition and carry forward values where missing. Underlying indicators differ by country and year; separate 2026 index from backdated annual estimates. Rankings and historical scores may be revised; consult methodology. Non-commercial, no-derivatives license applies.'}
    finally:
        w.close()

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('country')
    p.add_argument('start', type=int)
    p.add_argument('end', type=int)
    p.add_argument('--local-file')
    a = p.parse_args()
    print(json.dumps(query(a.country, a.start, a.end, a.local_file), ensure_ascii=False, indent=2))
if __name__ == '__main__':
    main()
