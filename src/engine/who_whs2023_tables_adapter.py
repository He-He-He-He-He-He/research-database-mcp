"""WHO World Health Statistics 2023 official historical annex workbook."""
import release_runtime
import argparse
import io
import json
import requests
import openpyxl
URL = 'https://cdn.who.int/media/docs/default-source/gho-documents/world-health-statistic-reports/2023/whs2023_annex1.xlsx?sfvrsn=30518d8e_3'
DOCUMENT = 'https://www.who.int/data/gho/publications/world-health-statistics'
SHEETS = ('Annex 1-1', 'Annex 1-2', 'Annex 1-3', 'Annex 1-4')
MAX_BYTES = 2000000

def query(country, sheet='all'):
    if not isinstance(country, str) or not 1 <= len(country.strip()) <= 100 or sheet not in ('all',) + SHEETS:
        raise ValueError('invalid country or sheet')
    with requests.get(URL, timeout=30, stream=True) as r:
        r.raise_for_status()
        raw = bytearray()
        for block in r.iter_content(65536):
            raw.extend(block)
            if len(raw) > MAX_BYTES:
                raise ValueError('workbook exceeds size limit')
    w = openpyxl.load_workbook(io.BytesIO(raw), read_only=True, data_only=True)
    try:
        if not set(SHEETS + ('Footnotes', 'Explanatory Notes')).issubset(w.sheetnames):
            raise ValueError('unexpected workbook sheets')
        tabs = []
        for name in SHEETS:
            if sheet != 'all' and name != sheet:
                continue
            s = w[name]
            headers = []
            records = []
            for n, row in enumerate(s.values, 1):
                if n <= 5:
                    headers.append({'row': n, 'cells': list(row)})
                elif isinstance(row[0], str) and row[0].strip().casefold() == country.strip().casefold():
                    records.append({'row': n, 'cells': list(row)})
            tabs.append({'sheet': name, 'headers': headers, 'records': records})
        notes = [{'row': n, 'cells': list(row)} for n, row in enumerate(w['Footnotes'].values, 1) if any((v is not None for v in row))]
        return {'source': URL, 'publication': DOCUMENT, 'report_page_date': '2023-05-19', 'workbook_explanatory_notes': [list(row) for row in w['Explanatory Notes'].values], 'country': country, 'tables': tabs, 'footnotes': notes, 'note': 'Workbook notes date 2023-05-23 differs from WHO report page 2023-05-19. Columns refer to different dates, populations, models or primary surveys; merged headers, footnote markers and missing symbols retain source positions. Verify original workbook before interpreting.'}
    finally:
        w.close()

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('country')
    p.add_argument('--sheet', choices=('all',) + SHEETS, default='all')
    a = p.parse_args()
    print(json.dumps(query(a.country, a.sheet), ensure_ascii=False, indent=2))
if __name__ == '__main__':
    main()
