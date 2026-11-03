"""US Treasury TIC monthly cross-border long-term securities positions."""
import release_runtime
import argparse, csv, io, json, re, requests
BASE = 'https://ticdata.treasury.gov/resource-center/data-chart-center/tic/Documents/'
TABLES = {'foreign_holds_us': ('slt_table1.txt', 'for_lt_total_pos'), 'us_holds_foreign': ('slt_table2.txt', 'us_lt_total_pos')}

def read(table):
    if table not in TABLES:
        raise ValueError('invalid table')
    u = BASE + TABLES[table][0]
    r = requests.get(u, timeout=60)
    r.raise_for_status()
    if len(r.content) > 5000000:
        raise ValueError('unexpected file size')
    rows = csv.reader(io.StringIO(r.content.decode('utf-8-sig')), delimiter='\t')
    headers = None
    out = []
    for row in rows:
        if headers is None:
            if row[:3] == ['country', 'country_code', 'date']:
                headers = row
                if TABLES[table][1] not in headers:
                    raise ValueError('unexpected columns')
            continue
        if len(row) < len(headers) or not re.fullmatch('\\d{4}-(?:0[1-9]|1[0-2])', row[2]):
            continue
        out.append(dict(zip(headers, (x.strip() for x in row[:len(headers)]))))
    if headers is None or not out:
        raise ValueError('no data in TIC table')
    return (out, u)

def countries(table, keyword=''):
    if not isinstance(keyword, str) or len(keyword) > 100:
        raise ValueError('invalid keyword')
    rows, u = read(table)
    pairs = {(x['country'], x['country_code']) for x in rows}
    out = [{'name': n, 'code': c} for n, c in sorted(pairs) if keyword.casefold() in (n + ' ' + c).casefold()]
    return {'source': u, 'matched_count': len(out), 'records': out}

def observations(table, country, start, end, limit=100):
    if not isinstance(country, str) or not 1 <= len(country) <= 100:
        raise ValueError('invalid country')
    if not isinstance(start, str) or not isinstance(end, str) or (not re.fullmatch('\\d{4}-(?:0[1-9]|1[0-2])', start)) or (not re.fullmatch('\\d{4}-(?:0[1-9]|1[0-2])', end)) or (start > end):
        raise ValueError('date must be YYYY-MM')
    if not 1 <= limit <= 1000:
        raise ValueError('invalid limit')
    data, u = read(table)
    rows = [x for x in data if country.casefold() in (x['country'].casefold(), x['country_code'].casefold()) and start <= x['date'] <= end]
    return {'source': u, 'provider': 'U.S. Treasury Treasury International Capital (TIC)', 'table': table, 'unit': 'million US dollars', 'matched_count': len(rows), 'records': rows[:limit], 'note': 'Position is a stock, net purchases/sales a flow, valuation change separate; geographic attribution differs by direction.'}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    s = p.add_subparsers(dest='cmd', required=True)
    c = s.add_parser('countries')
    c.add_argument('table', choices=TABLES)
    c.add_argument('--keyword', default='')
    q = s.add_parser('data')
    q.add_argument('table', choices=TABLES)
    q.add_argument('country')
    q.add_argument('start')
    q.add_argument('end')
    q.add_argument('--limit', type=int, default=100)
    a = p.parse_args()
    result = countries(a.table, a.keyword) if a.cmd == 'countries' else observations(a.table, a.country, a.start, a.end, a.limit)
    print(json.dumps(result, ensure_ascii=False, indent=2))
if __name__ == '__main__':
    main()
