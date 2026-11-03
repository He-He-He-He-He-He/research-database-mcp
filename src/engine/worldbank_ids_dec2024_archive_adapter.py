"""World Bank International Debt Statistics, December 2024 archived workbook."""
import release_runtime
import argparse
import io
import json
import re
import requests
import openpyxl
URL = 'https://thedocs.worldbank.org/en/doc/6e72b0ded996306fa01f5db7a0c38b19-0050052021/related/IDS2024-December2024.xlsx'
DOCUMENT = 'https://www.worldbank.org/en/programs/debt-statistics/publications'
MAX_BYTES = 40000000

def _book():
    with requests.get(URL, timeout=80, stream=True) as r:
        r.raise_for_status()
        raw = bytearray()
        for part in r.iter_content(131072):
            raw.extend(part)
            if len(raw) > MAX_BYTES:
                raise ValueError('workbook exceeds size limit')
    w = openpyxl.load_workbook(io.BytesIO(raw), read_only=True, data_only=True)
    needed = {'Data', 'Country - Metadata', 'Series - Metadata', 'Country-Series - Metadata', 'FootNote'}
    if not needed.issubset(w.sheetnames):
        w.close()
        raise ValueError('unexpected workbook structure')
    return w

def indicators(keyword='', limit=100):
    if not isinstance(keyword, str) or len(keyword) > 150 or isinstance(limit, bool) or (not isinstance(limit, int)) or (not 1 <= limit <= 500):
        raise ValueError('invalid keyword or limit')
    w = _book()
    try:
        rows = w['Series - Metadata'].values
        head = list(next(rows))
        out = []
        count = 0
        for row in rows:
            if not isinstance(row[0], str) or keyword.casefold() not in (str(row[0]) + ' ' + str(row[2])).casefold():
                continue
            count += 1
            if len(out) < limit:
                out.append(dict(zip(head, row)))
        return {'source': URL, 'archive_documentation': DOCUMENT, 'edition': 'December 2024', 'matched_count': count, 'returned': len(out), 'indicators': out, 'note': 'Original series metadata and data-source definitions retained. Publication month is from archive; do not assume every cell is directly observed.'}
    finally:
        w.close()

def data(iso3, indicator, start=2019, end=2023, counterpart='WLD', limit=100):
    if any((not isinstance(x, str) or not re.fullmatch('[A-Z]{3}', x) for x in (iso3, counterpart))):
        raise ValueError('invalid country or counterpart code')
    if not isinstance(indicator, str) or not re.fullmatch('[A-Za-z0-9_.]{1,80}', indicator):
        raise ValueError('invalid series code')
    if any((isinstance(x, bool) or not isinstance(x, int) for x in (start, end, limit))) or not 1970 <= start <= end <= 2031 or (not 1 <= limit <= 500):
        raise ValueError('invalid years or limit')
    w = _book()
    try:
        rows = w['Data'].values
        header = list(next(rows))
        expected = ['Country Name', 'Country Code', 'Counterpart-Area Name', 'Counterpart-Area Code', 'Series Name', 'Series Code']
        if header[:6] != expected:
            raise ValueError('unexpected Data header')
        years = [(i, c) for i, c in enumerate(header) if isinstance(c, int) and start <= c <= end]
        out = []
        count = 0
        for row in rows:
            if row[1] != iso3 or row[3] != counterpart or row[5] != indicator:
                continue
            count += 1
            if len(out) < limit:
                out.append({'country': row[0], 'country_code': row[1], 'counterpart': row[2], 'counterpart_code': row[3], 'series_name': row[4], 'series_code': row[5], 'observations': [{'year': y, 'raw_value': row[i]} for i, y in years]})

        def table_lookup(sheet, predicate):
            it = w[sheet].values
            h = list(next(it))
            return [dict(zip(h, r)) for r in it if predicate(r)]
        series = table_lookup('Series - Metadata', lambda r: r[0] == indicator)
        country = table_lookup('Country - Metadata', lambda r: r[0] == iso3)
        country_series = table_lookup('Country-Series - Metadata', lambda r: isinstance(r[1], str) and r[1].endswith('(' + iso3 + ')') and isinstance(r[2], str) and r[2].endswith('(' + indicator + ')'))
        footnotes = table_lookup('FootNote', lambda r: isinstance(r[1], str) and r[1].endswith('(' + iso3 + ')') and isinstance(r[2], str) and r[2].endswith('(' + indicator + ')'))
        return {'source': URL, 'archive_documentation': DOCUMENT, 'edition': 'December 2024', 'country': iso3, 'counterpart': counterpart, 'indicator': indicator, 'matched_count': count, 'returned': len(out), 'records': out, 'series_metadata': series, 'country_metadata': country, 'country_series_metadata': country_series, 'all_series_footnotes': footnotes, 'note': 'December 2024 archive; precise file publication time not inferred. Country, counterpart, units, staff estimates, projection horizons and relevant footnotes matter. Original null values remain null. Historical values can differ from current IDS.'}
    finally:
        w.close()

def main():
    p = argparse.ArgumentParser(description=__doc__)
    s = p.add_subparsers(dest='cmd', required=True)
    q = s.add_parser('indicators')
    q.add_argument('--keyword', default='')
    q.add_argument('--limit', type=int, default=100)
    q = s.add_parser('data')
    q.add_argument('iso3')
    q.add_argument('indicator')
    q.add_argument('--start', type=int, default=2019)
    q.add_argument('--end', type=int, default=2023)
    q.add_argument('--counterpart', default='WLD')
    q.add_argument('--limit', type=int, default=100)
    a = p.parse_args()
    out = indicators(a.keyword, a.limit) if a.cmd == 'indicators' else data(a.iso3, a.indicator, a.start, a.end, a.counterpart, a.limit)
    print(json.dumps(out, ensure_ascii=False, indent=2))
if __name__ == '__main__':
    main()
