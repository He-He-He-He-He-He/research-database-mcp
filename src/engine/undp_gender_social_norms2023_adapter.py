"""UNDP 2023 Gender Social Norms Index official tables."""
import release_runtime
import argparse, io, json, re, openpyxl, requests
URL = 'https://hdr.undp.org/sites/default/files/publications/additional-files/2023-06/GSNI2023_AnnexTables2.xlsx'
TABLES = {'latest': 'Table A1', 'sex': 'Table A2', 'trends': 'Table A3a', 'trends_sex': 'Table A3b'}

def query(country, table='latest', local_file=None):
    if not isinstance(country, str) or not re.fullmatch('[A-Z]{3}', country) or table not in TABLES:
        raise ValueError('invalid query')
    if local_file:
        w = openpyxl.load_workbook(local_file, read_only=True, data_only=True)
    else:
        r = requests.get(URL, timeout=45)
        r.raise_for_status()
        if len(r.content) > 1000000:
            raise ValueError('unexpected file size')
        w = openpyxl.load_workbook(io.BytesIO(r.content), read_only=True, data_only=True)
    try:
        s = w[TABLES[table]]
        header = []
        out = []
        for i, row in enumerate(s.values, 1):
            vals = list(row)
            while vals and vals[-1] is None:
                vals.pop()
            if i <= 6:
                header.append({'row': i, 'cells': vals})
            if vals and vals[0] == country:
                out.append({'row': i, 'cells': vals})
        return {'source': local_file if local_file else URL, 'provider': None if local_file else 'UNDP 2023 Gender Social Norms Index', 'table': table, 'header_context': header, 'matched_count': len(out), 'records': out, 'note': 'World Values Survey waves cover multi-year periods; values reflect specific survey questions, not direct measures of individual behavior.' + (' Local workbook provenance, version and interpretation are unverified.' if local_file else '')}
    finally:
        w.close()

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('country')
    p.add_argument('--table', choices=TABLES, default='latest')
    p.add_argument('--local-file')
    a = p.parse_args()
    print(json.dumps(query(a.country, a.table, a.local_file), ensure_ascii=False, indent=2))
if __name__ == '__main__':
    main()
