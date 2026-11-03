"""UNAIDS 2026 published HIV estimates and 95-95-95 treatment workbook."""
import release_runtime
import argparse, io, json, requests, openpyxl
URL = 'https://www.unaids.org/sites/default/files/2026-07/HIV_estimates_from_1990-to-present_1.xlsx'
SHEETS = {'estimates': 'HIV2026Estimates_ByYear', 'treatment': 'HIV-Test-&-Treat_ByYear'}

def query(area, year, topic='estimates', keyword=None):
    if topic not in SHEETS:
        raise ValueError('unknown topic')
    if not isinstance(area, str) or not 1 <= len(area) <= 80:
        raise ValueError('invalid area')
    if isinstance(year, bool) or not 1990 <= int(year) <= 2025:
        raise ValueError('year must be 1990–2025')
    if keyword is not None and (not isinstance(keyword, str) or len(keyword) > 100):
        raise ValueError('invalid keyword')
    with requests.get(URL, timeout=60, stream=True) as r:
        r.raise_for_status()
        data = []
        size = 0
        for c in r.iter_content(65536):
            size += len(c)
            if size > 15000000:
                raise ValueError('file exceeds 15 MB')
            data.append(c)
    w = openpyxl.load_workbook(io.BytesIO(b''.join(data)), read_only=True, data_only=True)
    try:
        s = w[SHEETS[topic]]
        headers = list(s.iter_rows(min_row=4, max_row=6, values_only=True))
        r4, r5, r6 = headers
        rows = []
        for row in s.iter_rows(min_row=7, values_only=True):
            if row[0] != int(year) or area.casefold() not in {str(row[1]).casefold(), str(row[2]).casefold()}:
                continue
            group = ''
            out = []
            for i in range(3, len(row), 3):
                if i >= len(r6) or r6[i] != 'Estimate':
                    continue
                if r4[i]:
                    group = str(r4[i]).strip()
                label = str(r5[i] or '').strip()
                full = ' '.join((x for x in (group, label) if x))
                if keyword and keyword.casefold() not in full.casefold():
                    continue
                out.append({'indicator': full, 'estimate': row[i], 'low': row[i + 1] if i + 1 < len(row) else None, 'high': row[i + 2] if i + 2 < len(row) else None})
            rows.append({'year': row[0], 'area_code': row[1], 'area_name': row[2], 'indicators': out})
        return {'provider': 'UNAIDS', 'edition': '2026 estimates', 'source': URL, 'topic': topic, 'matched_rows': len(rows), 'records': rows, 'note': 'Rounded estimates with uncertainty bounds as published; preserve symbols <, > and ... .'}
    finally:
        w.close()

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('area')
    p.add_argument('year', type=int)
    p.add_argument('--topic', choices=sorted(SHEETS), default='estimates')
    p.add_argument('--keyword')
    a = p.parse_args()
    print(json.dumps(query(a.area, a.year, a.topic, a.keyword), ensure_ascii=False, indent=2))
if __name__ == '__main__':
    main()
