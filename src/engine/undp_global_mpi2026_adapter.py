"""UNDP-OPHI Global Multidimensional Poverty Index 2026 published tables."""
import release_runtime
import argparse, io, json, openpyxl, requests
URL = 'https://hdr.undp.org/sites/default/files/publications/additional-files/2026-10/2026_gMPI_Table1and2.xlsx'
SHEETS = {'latest': 'gMPI2026_Table1', 'trends': 'gMPI2026_Table2'}

def query(country, table='latest', local_file=None):
    if not isinstance(country, str) or not 1 <= len(country) <= 100 or table not in SHEETS:
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
        s = w[SHEETS[table]]
        out = []
        for i, row in enumerate(s.values, 1):
            if not isinstance(row[0], str) or row[0].casefold() != country.casefold():
                continue
            if table == 'latest':
                d = {'survey': row[1], 'survey_note': row[2], 'mpi': row[3], 'mpi_note': row[4], 'headcount_percent': row[5], 'headcount_note': row[6], 'poor_thousands_survey_year': row[7], 'poor_thousands_2024': row[9], 'intensity_percent': row[11]}
            else:
                d = {'country_note': row[1], 'survey': row[2], 'survey_note': row[3], 'mpi': row[4], 'mpi_note': row[5], 'headcount_percent': row[6], 'headcount_note': row[7], 'poor_thousands_survey_year': row[8], 'intensity_percent': row[10]}
            d['row_number'] = i
            d['raw_columns'] = list(row)
            out.append(d)
        return {'source': local_file if local_file else URL, 'provider': None if local_file else 'UNDP and OPHI', 'table': table, 'matched_count': len(out), 'records': out, 'note': 'Table 2 harmonizes historical estimates for trend comparability and may differ from Table 1; consult workbook footnotes and survey dates.' + (' Local workbook provenance and version are unverified.' if local_file else '')}
    finally:
        w.close()

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('country')
    p.add_argument('--table', choices=SHEETS, default='latest')
    p.add_argument('--local-file')
    a = p.parse_args()
    print(json.dumps(query(a.country, a.table, a.local_file), ensure_ascii=False, indent=2))
if __name__ == '__main__':
    main()
