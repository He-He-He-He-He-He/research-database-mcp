"""US Treasury Monthly Treasury Statement selected tables, public API."""
import release_runtime
import argparse, datetime, json
import requests
ROOT = 'https://api.fiscaldata.treasury.gov/services/api/fiscal_service/v1/accounting/mts/'
TABLES = {'1': 'Summary of Receipts, Outlays and Deficit/Surplus', '4': 'Receipts of the US Government', '5': 'Outlays of the US Government', '9': 'Receipts by Source and Outlays by Function'}

def rows(table, start, end, page=1, page_size=20):
    if table not in TABLES:
        raise ValueError('table must be one of ' + ', '.join(TABLES))
    try:
        a = datetime.date.fromisoformat(start)
        b = datetime.date.fromisoformat(end)
    except ValueError:
        raise ValueError('dates must be YYYY-MM-DD') from None
    if a > b or (b - a).days > 366 or (not 1 <= page <= 10000) or (not 1 <= page_size <= 100):
        raise ValueError('invalid range or pagination')
    params = {'filter': f'record_date:gte:{start},record_date:lte:{end}', 'page[number]': page, 'page[size]': page_size, 'sort': '-record_date'}
    with requests.get(ROOT + 'mts_table_' + table, params=params, timeout=35, stream=True, headers={'User-Agent': 'ResearchToolkit/1.0'}) as r:
        r.raise_for_status()
        parts = []
        size = 0
        for c in r.iter_content(65536):
            size += len(c)
            if size > 8 * 1024 * 1024:
                raise ValueError('response exceeds 8 MiB')
            parts.append(c)
        data = json.loads(b''.join(parts))
        url = r.url
    if not isinstance(data.get('data'), list) or not isinstance(data.get('meta'), dict):
        raise ValueError('unexpected response')
    return {'source': url, 'table': TABLES[table], **data, 'note': 'Amounts are unmodified decimal strings. Record date is the publication/report period, while individual row labels can refer to earlier fiscal years or months.'}

def main():
    p = argparse.ArgumentParser()
    p.add_argument('table', choices=TABLES)
    p.add_argument('start')
    p.add_argument('end')
    p.add_argument('--page', type=int, default=1)
    p.add_argument('--page-size', type=int, default=20)
    a = p.parse_args()
    print(json.dumps(rows(a.table, a.start, a.end, a.page, a.page_size), ensure_ascii=False, indent=2))
if __name__ == '__main__':
    main()
