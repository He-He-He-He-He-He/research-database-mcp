"""World Bank Pink Sheet: bounded commodity search and monthly observations."""
import release_runtime
import argparse, io, json, re
import requests
try:
    import openpyxl
except ImportError as exc:
    raise ImportError('Install openpyxl to read World Bank XLSX') from exc
SOURCE = 'https://thedocs.worldbank.org/en/doc/74e8be41ceb20fa0da750cda2f6b9e4e-0050012026/related/CMO-Historical-Data-Monthly.xlsx'
LANDING = 'https://www.worldbank.org/en/research/commodity-markets'

def workbook():
    with requests.get(SOURCE, timeout=45, stream=True, headers={'User-Agent': 'ResearchToolkit/1.0'}) as response:
        response.raise_for_status()
        chunks = []
        size = 0
        for chunk in response.iter_content(65536):
            size += len(chunk)
            if size > 8 * 1024 * 1024:
                raise ValueError('Workbook exceeds 8 MiB')
            chunks.append(chunk)
    book = openpyxl.load_workbook(io.BytesIO(b''.join(chunks)), read_only=True, data_only=True)
    sheet = book['Monthly Prices']
    rows = sheet.iter_rows(values_only=True)
    title = next(rows)[0]
    next(rows)
    next(rows)
    updated = next(rows)[0]
    names = next(rows)
    units = next(rows)
    if not str(title).startswith('World Bank Commodity Price Data'):
        raise ValueError('Unexpected workbook layout')
    return (book, rows, names, units, updated)

def search(keyword='', limit=50, *, offset=0):
    if not isinstance(keyword, str) or len(keyword) > 100 or type(limit) is not int or (not 1 <= limit <= 100) or (type(offset) is not int) or (offset < 0):
        raise ValueError('invalid search')
    book, rows, names, units, updated = workbook()
    try:
        series = [{'name': n, 'unit': units[i]} for i, n in enumerate(names) if i and isinstance(n, str) and (keyword.casefold() in n.casefold())]
        return {'source': SOURCE, 'updated': updated, 'series': series[offset:offset + limit], 'total': len(series), 'offset': offset, 'returned': len(series[offset:offset + limit]), 'next_offset': offset + limit if offset + limit < len(series) else None, 'truncated': offset + limit < len(series), 'note': 'The workbook is refetched for each request; updates may change ordering.'}
    finally:
        book.close()

def observations(name, start='1960M01', end='9999M12', limit=100, *, offset=0):
    if not name or len(name) > 100 or (not 1 <= limit <= 1000) or (not all((re.fullmatch('\\d{4}M(0[1-9]|1[0-2])', x) for x in (start, end)))) or (start > end) or (type(offset) is not int) or (offset < 0):
        raise ValueError('invalid name, period, limit or offset')
    book, rows, names, units, updated = workbook()
    try:
        ids = [i for i, n in enumerate(names) if isinstance(n, str) and n.casefold() == name.casefold()]
        if len(ids) != 1:
            raise ValueError('Unknown or ambiguous commodity name; use search')
        idx = ids[0]
        data = []
        missing = []
        total = 0
        for row in rows:
            period = row[0]
            if not isinstance(period, str) or not re.fullmatch('\\d{4}M(0[1-9]|1[0-2])', period) or (not start <= period <= end):
                continue
            value = row[idx]
            if not isinstance(value, (int, float)) or isinstance(value, bool):
                missing.append({'period': period, 'raw_value': value})
                continue
            if offset <= total < offset + limit:
                data.append({'period': period, 'value': value})
            total += 1
        return {'source': SOURCE, 'updated': updated, 'name': names[idx], 'unit': units[idx], 'observations': data, 'total': total, 'missing_observations': missing, 'offset': offset, 'returned': len(data), 'next_offset': offset + limit if offset + limit < total else None, 'truncated': offset + limit < total, 'note': 'total counts numeric observations; missing_observations retains nonnumeric and blank source cells. Nominal US dollars; see workbook Description for definitions; workbook also contains Mismatch Details with differing cells whose provenance is not established. The workbook is refetched for each request and may change ordering.'}
    finally:
        book.close()

def main():
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest='cmd', required=True)
    s = sub.add_parser('search')
    s.add_argument('keyword', nargs='?', default='')
    s.add_argument('--limit', type=int, default=50)
    s.add_argument('--offset', type=int, default=0)
    s = sub.add_parser('observations')
    s.add_argument('name')
    s.add_argument('--start', default='1960M01')
    s.add_argument('--end', default='9999M12')
    s.add_argument('--limit', type=int, default=100)
    s.add_argument('--offset', type=int, default=0)
    a = p.parse_args()
    result = search(a.keyword, a.limit, offset=a.offset) if a.cmd == 'search' else observations(a.name, a.start, a.end, a.limit, offset=a.offset)
    print(json.dumps(result, ensure_ascii=False, indent=2))
if __name__ == '__main__':
    main()
