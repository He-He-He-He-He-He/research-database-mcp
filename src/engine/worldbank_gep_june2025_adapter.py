"""World Bank June 2025 GEP GDP workbook, preserving table context and notes."""
import release_runtime
import argparse
import io
import json
import requests
import openpyxl
URL = 'https://thedocs.worldbank.org/en/doc/8bf0b62ec6bcb886d97295ad930059e9-0050012025/related/GEP-June-2025-GDP-growth-data.xlsx'
DOCUMENT = 'https://thedocs.worldbank.org/en/doc/8bf0b62ec6bcb886d97295ad930059e9-0050012025/global-economic-prospects---june-2025'
MAX_BYTES = 1000000

def search(keyword, sheet='all', limit=50):
    if not isinstance(keyword, str) or not 2 <= len(keyword.strip()) <= 100 or isinstance(limit, bool) or (not isinstance(limit, int)) or (not 1 <= limit <= 100):
        raise ValueError('invalid keyword or limit')
    with requests.get(URL, timeout=30, stream=True) as r:
        r.raise_for_status()
        raw = bytearray()
        for block in r.iter_content(65536):
            raw.extend(block)
            if len(raw) > MAX_BYTES:
                raise ValueError('workbook exceeds size limit')
    w = openpyxl.load_workbook(io.BytesIO(raw), read_only=True, data_only=True)
    try:
        if sheet != 'all' and sheet not in w.sheetnames:
            raise ValueError('unknown sheet')
        results = []
        total = 0
        metadata = []
        for s in w:
            if sheet != 'all' and s.title != sheet:
                continue
            rows = list(s.values)
            heads = [{'row': i + 1, 'cells': list(r)} for i, r in enumerate(rows[:5])]
            notes = [{'row': i + 1, 'text': r[0]} for i, r in enumerate(rows) if isinstance(r[0], str) and r[0].strip().startswith('Source')]
            metadata.append({'sheet': s.title, 'headers': heads, 'notes': notes})
            for i, row in enumerate(rows):
                if not any((isinstance(c, str) and len(c) <= 120 and (keyword.casefold() in c.casefold()) for c in row[:5])):
                    continue
                total += 1
                if len(results) >= limit:
                    continue
                fiscal = None
                for j in range(i - 1, -1, -1):
                    if isinstance(rows[j][0], str) and 'fiscal year basis' in rows[j][0].casefold():
                        fiscal = {'row': j + 1, 'cells': list(rows[j])}
                        break
                    if any((isinstance(c, str) and c == '2024e' for c in rows[j])):
                        break
                results.append({'sheet': s.title, 'row': i + 1, 'raw_columns': list(row), 'preceding_rows': [{'row': j + 1, 'cells': list(rows[j])} for j in range(max(0, i - 2), i)], 'fiscal_year_header': fiscal})
        return {'source': URL, 'document': DOCUMENT, 'publication_date': '2025-06-10', 'edition': 'Global Economic Prospects June 2025', 'matching_rows': total, 'returned': len(results), 'sheet_metadata': metadata, 'results': results, 'note': 'Raw source rows, not independently harmonized. e=estimate; f=forecast. Rows may repeat across sections, columns may use fiscal rather than calendar years, and forecast revisions have separate headers. Read source notes and verify the original workbook.'}
    finally:
        w.close()

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('keyword')
    p.add_argument('--sheet', default='all')
    p.add_argument('--limit', type=int, default=50)
    a = p.parse_args()
    print(json.dumps(search(a.keyword, a.sheet, a.limit), ensure_ascii=False, indent=2))
if __name__ == '__main__':
    main()
