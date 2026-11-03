"""ILO Global Wage Report 2024–25 official data workbook."""
import release_runtime
import argparse, io, json, openpyxl, requests
URL = 'https://www.ilo.org/media/627781/download'
SHEETS = {'nominal': 'Nominal wage', 'real_growth': 'Real wage growth'}

def query(kind, country='', start=2017, end=2024, limit=100):
    if kind not in SHEETS or not isinstance(country, str) or len(country) > 100 or (not 2000 <= start <= end <= 2024) or (not 1 <= limit <= 500):
        raise ValueError('invalid query')
    r = requests.get(URL, timeout=45)
    r.raise_for_status()
    if len(r.content) > 1000000:
        raise ValueError('unexpected file size')
    w = openpyxl.load_workbook(io.BytesIO(r.content), read_only=True, data_only=True)
    try:
        it = w[SHEETS[kind]].values
        h = next(it)
        name, code = ('countryname', 'ccode') if kind == 'nominal' else ('country_name', 'ISO')
        if name not in h or code not in h or 2023 not in h:
            raise ValueError('unexpected schema')
        out = []
        count = 0
        for row in it:
            d = dict(zip(h, row))
            if not isinstance(d.get(name), str) or (country and country.casefold() not in (d[name].casefold(), str(d.get(code, '')).casefold())):
                continue
            count += 1
            if len(out) < limit:
                out.append({'metadata': {k: v for k, v in d.items() if isinstance(k, str)}, 'values': {str(k): v for k, v in d.items() if isinstance(k, int) and start <= k <= end}})
        return {'source': URL, 'publication_date': '2024-11-28', 'kind': kind, 'matched_count': count, 'records': out, 'note': 'Nominal monthly wage local currency; real growth percent. Blank and null mean missing; data and revisions differ from earlier vintages.'}
    finally:
        w.close()

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('kind', choices=SHEETS)
    p.add_argument('--country', default='')
    p.add_argument('--start', type=int, default=2017)
    p.add_argument('--end', type=int, default=2024)
    p.add_argument('--limit', type=int, default=100)
    a = p.parse_args()
    print(json.dumps(query(a.kind, a.country, a.start, a.end, a.limit), ensure_ascii=False, indent=2))
if __name__ == '__main__':
    main()
