"""WHO World Malaria Report 2024: original estimate and reported-data tables."""
import release_runtime
import argparse
import io
import json
import requests
import openpyxl
BASE = 'https://cdn.who.int/media/docs/default-source/malaria/world-malaria-reports/'
SOURCES = {'estimated': ('wmr2024_annex_4f.xlsx?sfvrsn=1a59a8ac_4', 'Annex4F_allyears', 3, 2772), 'reported_cases': ('wmr2024_annex_4g.xlsx?sfvrsn=c1b6ba3c_3', 'Annex_4G', 5, 109), 'reported_deaths': ('wmr2024_annex_4j.xlsx?sfvrsn=74985cd_4', 'Annex_4J', 3, 117)}
DOCUMENT = 'https://www.who.int/publications/m/item/annexes-world-malaria-report-2024'
MAX_BYTES = 2000000

def query(keyword, kind='estimated', year=None, limit=100):
    if not isinstance(keyword, str) or not 2 <= len(keyword.strip()) <= 100 or kind not in SOURCES:
        raise ValueError('invalid keyword or source')
    if year is not None and (kind != 'estimated' or isinstance(year, bool) or (not isinstance(year, int)) or (not 2000 <= year <= 2023)):
        raise ValueError('year filtering only supported for estimated table, 2000–2023')
    if isinstance(limit, bool) or not isinstance(limit, int) or (not 1 <= limit <= 500):
        raise ValueError('invalid limit')
    filename, sheet, header_end, footer_start = SOURCES[kind]
    url = BASE + filename
    with requests.get(url, timeout=30, stream=True) as r:
        r.raise_for_status()
        raw = bytearray()
        for block in r.iter_content(65536):
            raw.extend(block)
            if len(raw) > MAX_BYTES:
                raise ValueError('workbook exceeds size limit')
    w = openpyxl.load_workbook(io.BytesIO(raw), read_only=True, data_only=True)
    try:
        s = w[sheet]
        rows = list(s.values)
        headers = [{'row': n + 1, 'cells': list(row)} for n, row in enumerate(rows[:header_end])]
        notes = []
        out = []
        count = 0
        country = None
        anchors = {'estimated': 'NMP:', 'reported_cases': 'RDT:', 'reported_deaths': 'E-2025:'}
        if len(rows) < footer_start or not isinstance(rows[footer_start - 1][0], str) or (not rows[footer_start - 1][0].startswith(anchors[kind])):
            raise ValueError('unexpected footer position; check source version')
        for i, row in enumerate(rows[header_end:], header_end + 1):
            if i >= footer_start:
                if any((v is not None for v in row)):
                    notes.append({'row': i, 'cells': list(row)})
                continue
            first = row[0]
            if kind == 'estimated':
                if isinstance(first, str) and first.strip():
                    country = first.strip()
                if not isinstance(row[1], int) or not 2000 <= row[1] <= 2023 or country is None:
                    continue
                if keyword.casefold() not in country.casefold() or (year is not None and year != row[1]):
                    continue
            else:
                if not isinstance(first, str) or not first.strip() or keyword.casefold() not in first.casefold():
                    continue
                country = first.strip()
            count += 1
            if len(out) < limit:
                out.append({'row': i, 'country_label': country, 'country_label_inherited': kind == 'estimated' and (not bool(first)), 'raw_columns': list(row)})
        return {'source': url, 'publication': DOCUMENT, 'report_published': '2024-12-11', 'kind': kind, 'sheet': sheet, 'headers': headers, 'matched_count': count, 'returned': len(out), 'records': out, 'notes': notes, 'note': 'Estimated cases/deaths are model estimates and uncertainty bounds; reported cases/deaths are separate series and cannot be substituted. In 4F the dash in lower/upper bounds can mean equal to point estimate, as source notes explain. Country labels can contain footnote numbers; matched labels and raw cells are preserved.'}
    finally:
        w.close()

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('keyword')
    p.add_argument('--kind', choices=SOURCES, default='estimated')
    p.add_argument('--year', type=int)
    p.add_argument('--limit', type=int, default=100)
    a = p.parse_args()
    print(json.dumps(query(a.keyword, a.kind, a.year, a.limit), ensure_ascii=False, indent=2))
if __name__ == '__main__':
    main()
