"""World Bank Business Ready 2024 revised April 2025 pillar scores and corrections."""
import release_runtime
import argparse, hashlib, io, json, zipfile
import requests, openpyxl
URL = 'https://www.worldbank.org/content/dam/sites/b-ready/documents/excel/B-READY_ALL_DATA_2024.zip'
FILE = '01_Scored economies/01_B-READY-2024-PILLAR-TOPIC-SCORES-2024.xlsx'
PAGE = 'https://www.worldbank.org/en/businessready/reports'

def query(country='', kind='pillars', limit=50):
    if not isinstance(country, str) or len(country) > 100 or kind not in ('pillars', 'corrections') or (type(limit) is not int) or (not 1 <= limit <= 500):
        raise ValueError('invalid query')
    with requests.get(URL, stream=True, timeout=60) as r:
        r.raise_for_status()
        modified = r.headers.get('Last-Modified')
        raw = r.raw.read(10000001, decode_content=True)
    if len(raw) > 10000000:
        raise ValueError('archive too large')
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        info = z.getinfo(FILE)
        if info.file_size > 5000000:
            raise ValueError('workbook too large')
        data = z.read(info)
    w = openpyxl.load_workbook(io.BytesIO(data), read_only=True, data_only=True)
    try:
        if kind == 'pillars':
            sheet = w['00_B-READY_Pillar_Score']
            it = sheet.iter_rows(values_only=True)
            headers = next(it)
            rows = []
            count = 0
            for row in it:
                if not isinstance(row[0], str):
                    continue
                if country and country.casefold() not in (row[0].casefold(), str(row[1]).casefold()):
                    continue
                count += 1
                if len(rows) < limit:
                    rows.append({headers[i]: row[i] for i in range(5)})
        else:
            sheet = w['CORRECTIONS']
            it = sheet.iter_rows(values_only=True)
            next(it)
            headers = next(it)
            rows = []
            count = 0
            for row in it:
                if not any((v is not None for v in row)):
                    continue
                if country and (not any((country.casefold() in str(v).casefold() for v in row if v is not None))):
                    continue
                count += 1
                if len(rows) < limit:
                    rows.append([{'column': i + 1, 'heading': headers[i] if i < len(headers) else None, 'value': v} for i, v in enumerate(row) if v is not None])
        return {'source': URL, 'source_page': PAGE, 'edition': 'Business Ready 2024', 'workbook_reported_version': '2025-04-11', 'workbook_internal_modified': str(w.properties.modified), 'archive_http_last_modified': modified, 'archive_sha256': hashlib.sha256(raw).hexdigest(), 'workbook_sha256': hashlib.sha256(data).hexdigest(), 'kind': kind, 'matched_count': count, 'records': rows, 'note': 'This is the subsequently corrected April 2025 version of a report first published 2024-10-03, not its initial release. Covers 50 scored economies; no match does not mean zero. Separate pillars measure regulatory framework, public services, operational efficiency; do not combine or imply legal compliance or a worldwide ranking. Corrections retain original sparse column headings; inspect workbook for full context. Timestamps do not prove immutable archive; check source reuse terms.'}
    finally:
        w.close()

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--country', default='')
    p.add_argument('--kind', choices=['pillars', 'corrections'], default='pillars')
    p.add_argument('--limit', type=int, default=50)
    a = p.parse_args()
    print(json.dumps(query(a.country, a.kind, a.limit), ensure_ascii=False, indent=2))
if __name__ == '__main__':
    main()
