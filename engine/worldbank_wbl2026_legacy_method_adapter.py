"""World Bank Women, Business and the Law 2026 scores recalculated under WBL 1.0."""
import release_runtime
import argparse, io, json, re, openpyxl, requests
URL = 'https://datacatalogfiles.worldbank.org/ddh-published/0038489/DR0095940/2026-02-13-WBL-2026-1-0-Scores-Values.xlsx'

def query(country):
    if not isinstance(country, str) or not re.fullmatch('[A-Z]{3}', country):
        raise ValueError('country must be ISO3')
    r = requests.get(URL, timeout=45)
    r.raise_for_status()
    if len(r.content) > 1000000:
        raise ValueError('unexpected file size')
    w = openpyxl.load_workbook(io.BytesIO(r.content), read_only=True, data_only=True)
    try:
        it = w['WBL 2026 1.0'].values
        h = next(it)
        if tuple(h[:7]) != ('Economy', 'Economy Code', 'ISO Code', 'Region', 'Income Group', 'Report Year', 'WBL 1.0 INDEX'):
            raise ValueError('unexpected schema')
        rows = []
        for row in it:
            if row[2] == country:
                rows.append({'economy': row[0], 'iso_code': row[2], 'region': row[3], 'income_group': row[4], 'report_year': row[5], 'fields': [{'column': i + 1, 'label': k, 'value': row[i]} for i, k in enumerate(h) if i >= 6 and k is not None]})
        return {'source': URL, 'method': 'WBL 1.0', 'matched_count': len(rows), 'records': rows, 'note': 'Report year 2026, legacy 1.0 method. Catalog and workbook disagree on as-of date; verify authoritative edition before legal use.'}
    finally:
        w.close()

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('country')
    a = p.parse_args()
    print(json.dumps(query(a.country), ensure_ascii=False, indent=2))
if __name__ == '__main__':
    main()
