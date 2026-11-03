"""US Treasury TIC monthly Treasury securities held by foreign residents."""
import release_runtime
import argparse, csv, io, json, re, requests
URL = 'https://ticdata.treasury.gov/resource-center/data-chart-center/tic/Documents/slt_table3.txt'
HEAD = ['country', 'country_code', 'date', 'for_treas_pos', 'for_treas_net', 'for_lt_treas_pos', 'for_lt_treas_net', 'for_lt_treas_valchg', 'for_st_treas_pos', 'for_st_treas_net']

def read():
    r = requests.get(URL, timeout=50)
    r.raise_for_status()
    if len(r.content) > 5000000:
        raise ValueError('unexpected file size')
    rows = csv.reader(io.StringIO(r.content.decode('utf-8-sig')), delimiter='\t')
    found = False
    out = []
    for row in rows:
        if not found:
            if row[:len(HEAD)] == HEAD:
                found = True
            continue
        if len(row) < len(HEAD) or not re.fullmatch('\\d{4}-(?:0[1-9]|1[0-2])', row[2]):
            continue
        out.append(dict(zip(HEAD, (x.strip() for x in row[:len(HEAD)]))))
    if not found or not out:
        raise ValueError('unexpected Treasury table format')
    return out

def countries(keyword=''):
    if not isinstance(keyword, str) or len(keyword) > 100:
        raise ValueError('invalid keyword')
    pairs = {(x['country'], x['country_code']) for x in read()}
    out = [{'name': n, 'code': c} for n, c in sorted(pairs) if keyword.casefold() in (n + ' ' + c).casefold()]
    return {'source': URL, 'matched_count': len(out), 'records': out}

def observations(country, start, end, limit=100):
    if not isinstance(country, str) or not 1 <= len(country) <= 100:
        raise ValueError('invalid country')
    if not isinstance(start, str) or not isinstance(end, str) or (not re.fullmatch('\\d{4}-(?:0[1-9]|1[0-2])', start)) or (not re.fullmatch('\\d{4}-(?:0[1-9]|1[0-2])', end)) or (start > end):
        raise ValueError('date must be YYYY-MM')
    if not 1 <= limit <= 1000:
        raise ValueError('invalid limit')
    rows = [x for x in read() if country.casefold() in (x['country'].casefold(), x['country_code'].casefold()) and start <= x['date'] <= end]
    return {'source': URL, 'provider': 'U.S. Treasury Treasury International Capital (TIC)', 'unit': 'million US dollars', 'matched_count': len(rows), 'records': rows[:limit], 'note': 'Custodial reporting location may not be beneficial-owner nationality; holdings are stocks and net sales are flows. Empty values are not zero.'}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    s = p.add_subparsers(dest='cmd', required=True)
    c = s.add_parser('countries')
    c.add_argument('--keyword', default='')
    q = s.add_parser('data')
    q.add_argument('country')
    q.add_argument('start')
    q.add_argument('end')
    q.add_argument('--limit', type=int, default=100)
    a = p.parse_args()
    result = countries(a.keyword) if a.cmd == 'countries' else observations(a.country, a.start, a.end, a.limit)
    print(json.dumps(result, ensure_ascii=False, indent=2))
if __name__ == '__main__':
    main()
