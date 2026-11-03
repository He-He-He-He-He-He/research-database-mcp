"""IMF October 2026 WEO workbook country groups, commodity prices, and composition."""
import release_runtime
import argparse, datetime, io, json, openpyxl, requests
URL = 'https://data.imf.org/-/media/iData/External-Storage/Documents/0FA3DC49A04D446E9D69DBEB29979E1C/en/WEOOct2026all.xlsx'

def query(kind, group='', indicator='', start=2020, end=2031, limit=20, local_file=None):
    if kind not in ('groups', 'commodities', 'composition') or not isinstance(group, str) or (not isinstance(indicator, str)) or (len(group) > 100) or (len(indicator) > 100) or (not 1980 <= start <= end <= 2100) or (not 1 <= limit <= 1000):
        raise ValueError('invalid query')
    if local_file:
        w = openpyxl.load_workbook(local_file, read_only=True, data_only=True)
    else:
        r = requests.get(URL, timeout=90)
        r.raise_for_status()
        if len(r.content) > 15000000:
            raise ValueError('unexpected file size')
        w = openpyxl.load_workbook(io.BytesIO(r.content), read_only=True, data_only=True)
    try:
        sheet = {'groups': 'Country Groups', 'commodities': 'Commodity Prices', 'composition': 'Country Group Composition'}[kind]
        it = w[sheet].iter_rows(values_only=True)
        h = next(it)
        need = {'groupcode', 'groupname', 'countrycode', 'countryname'} if kind == 'composition' else {'COUNTRY.ID', 'COUNTRY', 'INDICATOR.ID', 'INDICATOR', 'UNIT', 'SCALE'}
        if not need.issubset(h):
            raise ValueError('unexpected workbook schema')
        out = []
        total = 0
        for row in it:
            d = dict(zip(h, row))
            gc = ('groupcode', 'groupname') if kind == 'composition' else ('COUNTRY.ID', 'COUNTRY')
            if group and group.casefold() not in [str(d[k]).casefold() for k in gc]:
                continue
            if kind == 'composition':
                if indicator and indicator.casefold() not in [str(d[k]).casefold() for k in ('countrycode', 'countryname')]:
                    continue
            elif indicator and indicator.casefold() not in [str(d[k]).casefold() for k in ('INDICATOR.ID', 'INDICATOR')]:
                continue
            total += 1
            if len(out) >= limit:
                continue
            meta = {str(k): v.isoformat() if isinstance(v, (datetime.date, datetime.datetime)) else v for k, v in d.items() if isinstance(k, str)}
            out.append({'metadata': meta, 'values': {str(k): v for k, v in d.items() if isinstance(k, int) and start <= k <= end}} if kind != 'composition' else meta)
        return {'source': local_file if local_file else URL, 'workbook_vintage': None if local_file else 'October 2026', 'kind': kind, 'matched_count': total, 'records': out, 'note': 'Later years may include projections. Group and commodity rows may not supply an actual/projection cutoff; verify IMF methodology.' + (' Local workbook provenance and version are unverified.' if local_file else '')}
    finally:
        w.close()

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('kind', choices=['groups', 'commodities', 'composition'])
    p.add_argument('--group', default='')
    p.add_argument('--indicator', default='')
    p.add_argument('--start', type=int, default=2020)
    p.add_argument('--end', type=int, default=2031)
    p.add_argument('--limit', type=int, default=20)
    p.add_argument('--local-file')
    a = p.parse_args()
    print(json.dumps(query(a.kind, a.group, a.indicator, a.start, a.end, a.limit, a.local_file), ensure_ascii=False, indent=2))
if __name__ == '__main__':
    main()
