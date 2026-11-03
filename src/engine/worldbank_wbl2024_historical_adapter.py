"""World Bank Women, Business and the Law 2024 version 2.0 workbook."""
import release_runtime
import argparse, hashlib, io, json, re
import requests, openpyxl
from openpyxl.utils import get_column_letter
URL = 'https://wbl.worldbank.org/content/dam/sites/wbl/documents/2024/WBL2024-2-0.xlsx'
PAGE = 'https://wbl.worldbank.org/en/data/download-data'
SHEETS = {'legal': ('Legal2.0', 1), 'support': ('SF2.0', 1), 'expert': ('EO_ByEconomy', 2)}

def query(code, sheet='legal'):
    if not isinstance(code, str) or not re.fullmatch('[A-Z]{3}', code):
        raise ValueError('provide three-letter economy code')
    if sheet not in SHEETS:
        raise ValueError('invalid sheet')
    with requests.get(URL, stream=True, timeout=30) as r:
        r.raise_for_status()
        modified = r.headers.get('Last-Modified')
        raw = r.raw.read(5000001, decode_content=True)
    if len(raw) > 5000000:
        raise ValueError('workbook exceeds size limit')
    w = openpyxl.load_workbook(io.BytesIO(raw), read_only=True, data_only=True)
    try:
        name, header_row = SHEETS[sheet]
        sh = w[name]
        rows = sh.iter_rows(values_only=True)
        for _ in range(header_row):
            headers = next(rows)
        if headers[0] != 'Economy' or headers[1] not in ('EconomyCode', 'Economy Code'):
            raise ValueError('unexpected source headers')
        hits = []
        for row in rows:
            if len(row) > 1 and row[1] == code:
                hits.append([{'column': get_column_letter(i + 1), 'heading': h, 'value': row[i] if i < len(row) else None} for i, h in enumerate(headers) if h is not None])
        if len(hits) > 1:
            raise ValueError('duplicate economy code')
        return {'source': URL, 'source_page': PAGE, 'file_version': '2024-03-04', 'http_last_modified': modified, 'source_sha256': hashlib.sha256(raw).hexdigest(), 'sheet': name, 'economy_code': code, 'found': bool(hits), 'fields': hits[0] if hits else [], 'note': 'World Bank WBL 2024 version 2.0; legal and supportive frameworks and expert opinions are separate concepts, not direct measures of lived equality. Expert sheet covers 164 economies, not all 190. The dataset reflects the legal assessment period, not current law; verify dates and legal basis in the source. Repeated headings are preserved by column. Numeric scores and survey measures must be interpreted using each original heading and methodology. Server modification timestamp does not prove immutable archival identity. CC BY 4.0 source attribution applies.'}
    finally:
        w.close()

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('code')
    p.add_argument('--sheet', choices=list(SHEETS), default='legal')
    a = p.parse_args()
    print(json.dumps(query(a.code, a.sheet), ensure_ascii=False, indent=2))
if __name__ == '__main__':
    main()
