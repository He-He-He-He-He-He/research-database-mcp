"""Global Findex 2021 country-level workbook published by World Bank in 2022."""
import release_runtime
import argparse
import io
import json
import re
import openpyxl
import requests
URL = 'https://thedocs.worldbank.org/en/doc/6fa0abd1f7f266f7115adae07278eb97-0050062022/original/Databank-wide.xlsx'
DOCUMENT = 'https://thedocs.worldbank.org/en/doc/6fa0abd1f7f266f7115adae07278eb97-0050062022/global-findex-2021-country-level-data-excel-file'
MAX_BYTES = 8000000

def _book():
    with requests.get(URL, timeout=40, stream=True) as response:
        response.raise_for_status()
        raw = bytearray()
        for block in response.iter_content(65536):
            raw.extend(block)
            if len(raw) > MAX_BYTES:
                raise ValueError('workbook exceeds size limit')
    return openpyxl.load_workbook(io.BytesIO(raw), read_only=True, data_only=True)

def indicators(keyword='', limit=100):
    if not isinstance(keyword, str) or len(keyword) > 150 or (not 1 <= limit <= 500):
        raise ValueError('invalid keyword or limit')
    book = _book()
    try:
        rows = book['Series_Table'].values
        header = next(rows)
        results = []
        count = 0
        for row in rows:
            if keyword.casefold() not in str(row[0]).casefold() + ' ' + str(row[1]).casefold():
                continue
            count += 1
            if len(results) < limit:
                results.append(dict(zip(header, row)))
        return {'source': URL, 'document': DOCUMENT, 'edition': '2021', 'matched_count': count, 'returned': len(results), 'indicators': results, 'note': 'Metadata codes use dots; Data sheet column codes generally use underscores. Verify the exact column and unit.'}
    finally:
        book.close()

def data(iso3, indicator, start=2011, end=2021):
    if not isinstance(iso3, str) or not re.fullmatch('[A-Z]{3}', iso3):
        raise ValueError('ISO3 must be uppercase')
    if not isinstance(indicator, str) or not re.fullmatch('[A-Za-z0-9_]{1,100}', indicator):
        raise ValueError('invalid Data sheet column')
    if any((isinstance(x, bool) or not isinstance(x, int) or x < 2011 or (x > 2021) for x in (start, end))) or start > end:
        raise ValueError('years must be within 2011–2021')
    book = _book()
    try:
        rows = book['Data'].values
        header = next(rows)
        labels = next(rows)
        if indicator not in header:
            raise ValueError('unknown Data sheet column')
        col = header.index(indicator)
        out = []
        for row in rows:
            if row[1] == iso3 and isinstance(row[3], int) and (start <= row[3] <= end):
                out.append({'country': row[0], 'iso3': row[1], 'adult_population': row[2], 'survey_year': row[3], 'region': row[4], 'income_group': row[5], 'raw_value': row[col]})
        meta_rows = book['Series_Table'].values
        meta_header = next(meta_rows)
        meta = [dict(zip(meta_header, row)) for row in meta_rows if isinstance(row[0], str) and row[0].replace('.', '_') == indicator]
        return {'source': URL, 'document': DOCUMENT, 'edition': '2021', 'document_web_publication': '2022-06-29', 'indicator_column': indicator, 'indicator_label': labels[col], 'indicator_metadata': meta, 'records': out, 'note': 'Values are raw workbook cells. Many percentage indicators are stored as fractions from 0 to 1; verify indicator metadata before conversion. Estimates come from surveys and can be missing; age/sex groups and survey years differ.'}
    finally:
        book.close()

def main():
    p = argparse.ArgumentParser(description=__doc__)
    s = p.add_subparsers(dest='cmd', required=True)
    q = s.add_parser('indicators')
    q.add_argument('--keyword', default='')
    q.add_argument('--limit', type=int, default=100)
    q = s.add_parser('data')
    q.add_argument('iso3')
    q.add_argument('indicator')
    q.add_argument('--start', type=int, default=2011)
    q.add_argument('--end', type=int, default=2021)
    a = p.parse_args()
    out = indicators(a.keyword, a.limit) if a.cmd == 'indicators' else data(a.iso3, a.indicator, a.start, a.end)
    print(json.dumps(out, ensure_ascii=False, indent=2))
if __name__ == '__main__':
    main()
