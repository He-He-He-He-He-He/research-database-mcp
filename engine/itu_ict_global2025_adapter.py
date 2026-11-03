"""ITU 2025 regional and global ICT indicator aggregates (research use)."""
import release_runtime
import argparse, io, json, requests, openpyxl
URL = 'https://www.itu.int/en/ITU-D/Statistics/Documents/facts/ITU_regional_global_Key_ICT_indicator_aggregates_Nov_2025.xlsx'
SHEETS = {'development': 'By dvpmnt status and spec. reg.', 'region': 'By BDT region'}

def query(scope, area, year, keyword=None):
    if scope not in SHEETS:
        raise ValueError('scope must be development or region')
    if not isinstance(area, str) or not 1 <= len(area) <= 100:
        raise ValueError('invalid area')
    if isinstance(year, bool) or not 2005 <= int(year) <= 2025:
        raise ValueError('year must be 2005–2025')
    if keyword is not None and (not isinstance(keyword, str) or len(keyword) > 100):
        raise ValueError('invalid keyword')
    with requests.get(URL, timeout=60, stream=True) as r:
        r.raise_for_status()
        chunks = []
        n = 0
        for b in r.iter_content(65536):
            n += len(b)
            if n > 5000000:
                raise ValueError('file exceeds 5 MB')
            chunks.append(b)
    w = openpyxl.load_workbook(io.BytesIO(b''.join(chunks)), read_only=True, data_only=True)
    try:
        s = w[SHEETS[scope]]
        rows = list(s.iter_rows(values_only=True))
        out = []
        indicator = None
        units = None
        for row in rows:
            if len(row) < 44:
                continue
            if isinstance(row[0], str) and row[1] == 'Millions' and (row[23] in ('Percentage', 'Per 100 inhabitants ')):
                indicator = row[0]
                units = [str(row[1]).strip(), str(row[23]).strip()]
                continue
            if indicator and str(row[0]).strip().casefold() == area.casefold():
                if keyword and keyword.casefold() not in indicator.casefold():
                    continue
                i = 1 + int(year) - 2005
                j = 23 + int(year) - 2005
                out.append({'indicator': indicator, 'area': row[0], 'year': int(year), 'measurements': [{'unit': units[0], 'value': row[i]}, {'unit': units[1], 'value': row[j]}]})
        return {'provider': 'International Telecommunication Union', 'release': 'November 2025', 'source': URL, 'scope': scope, 'matched_count': len(out), 'records': out, 'note': 'Regional aggregate estimates; missing and suppression markers preserved. Not national observations.'}
    finally:
        w.close()

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('scope', choices=sorted(SHEETS))
    p.add_argument('area')
    p.add_argument('year', type=int)
    p.add_argument('--keyword')
    a = p.parse_args()
    print(json.dumps(query(a.scope, a.area, a.year, a.keyword), ensure_ascii=False, indent=2))
if __name__ == '__main__':
    main()
