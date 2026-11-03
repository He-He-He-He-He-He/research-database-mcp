"""ILO Global Wage Report data workbook published 12 June 2023."""
import release_runtime
import argparse, io, json, openpyxl, requests
URL = 'https://www.ilo.org/media/363041/download'
SHEETS = {'nominal': 'Nomimal monthly wage (LCU) ', 'real_growth': 'Real wage growth estimates'}

def query(kind, country='', start=2006, end=2022, limit=100):
    if kind not in SHEETS or not isinstance(country, str) or len(country) > 100 or (not 2006 <= start <= end <= 2022) or (not 1 <= limit <= 500):
        raise ValueError('invalid query')
    r = requests.get(URL, timeout=45)
    r.raise_for_status()
    if len(r.content) > 1000000:
        raise ValueError('unexpected file size')
    w = openpyxl.load_workbook(io.BytesIO(r.content), read_only=True, data_only=True)
    try:
        it = w[SHEETS[kind]].values
        h = next(it)
        field = 'Country name' if kind == 'nominal' else 'country_name'
        if field not in h or 2022 not in h:
            raise ValueError('unexpected schema')
        result = []
        count = 0
        for row in it:
            d = dict(zip(h, row))
            name = d.get(field)
            if not isinstance(name, str) or (country and country.casefold() not in (name.casefold(), str(d.get('ISO', '')).casefold())):
                continue
            count += 1
            if len(result) < limit:
                result.append({'metadata': {k: v for k, v in d.items() if isinstance(k, str)}, 'values': {str(k): v for k, v in d.items() if isinstance(k, int) and start <= k <= end}})
        return {'source': URL, 'publication_date': '2023-06-12', 'kind': kind, 'matched_count': count, 'records': result, 'note': 'Historical data: nominal monthly amounts in local currency; real growth rates in percent. Check underlying national source and coverage.'}
    finally:
        w.close()

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('kind', choices=SHEETS)
    p.add_argument('--country', default='')
    p.add_argument('--start', type=int, default=2006)
    p.add_argument('--end', type=int, default=2022)
    p.add_argument('--limit', type=int, default=100)
    a = p.parse_args()
    print(json.dumps(query(a.kind, a.country, a.start, a.end, a.limit), ensure_ascii=False, indent=2))
if __name__ == '__main__':
    main()
