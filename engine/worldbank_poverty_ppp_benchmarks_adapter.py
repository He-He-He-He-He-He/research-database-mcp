"""World Bank purchasing power parities used in global poverty monitoring."""
import release_runtime
import argparse, io, json, re, openpyxl, requests
URL = 'https://datacatalogfiles.worldbank.org/ddh-published/0066851/DR0095348/Price_indices_for_global_poverty_monitoring.xlsx'
SHEETS = ('2021ppp', 'revised_2011ppp', '2017ppp', 'revised_2017ppp')

def query(vintage='2021ppp', country='', limit=100, *, offset=0):
    if vintage not in SHEETS or not isinstance(country, str) or (country and (not re.fullmatch('[A-Z]{3}', country))) or (type(limit) is not int) or (not 1 <= limit <= 1000) or (type(offset) is not int) or (offset < 0):
        raise ValueError('invalid query')
    r = requests.get(URL, timeout=45)
    r.raise_for_status()
    if len(r.content) > 1000000:
        raise ValueError('unexpected file size')
    w = openpyxl.load_workbook(io.BytesIO(r.content), read_only=True, data_only=True)
    try:
        it = w[vintage].values
        h = next(it)
        if not {'country_name', 'country_code', 'in_pip', 'reporting_level', 'source', 'method', 'note'}.issubset(h):
            raise ValueError('unexpected schema')
        rows = [dict(zip(h, row)) for row in it if not country or row[h.index('country_code')] == country]
        return {'source': URL, 'vintage': vintage, 'matched_count': len(rows), 'offset': offset, 'returned': len(rows[offset:offset + limit]), 'next_offset': offset + limit if offset + limit < len(rows) else None, 'truncated': offset + limit < len(rows), 'records': rows[offset:offset + limit], 'note': 'Revised 2017 PPPs were not adopted for global poverty monitoring; preserve original and PIP adjusted estimates separately. Each request refetches the workbook; source updates may change ordering. Blank cells remain null, not zero.'}
    finally:
        w.close()

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--vintage', choices=SHEETS, default='2021ppp')
    p.add_argument('--country', default='')
    p.add_argument('--limit', type=int, default=100)
    p.add_argument('--offset', type=int, default=0)
    a = p.parse_args()
    print(json.dumps(query(a.vintage, a.country, a.limit, offset=a.offset), ensure_ascii=False, indent=2))
if __name__ == '__main__':
    main()
