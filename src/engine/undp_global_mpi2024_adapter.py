"""UNDP/OPHI 2024 global MPI published workbook; no survey microdata."""
import release_runtime
import argparse
import io
import json
import openpyxl
import requests
URL = 'https://hdr.undp.org/sites/default/files/publications/additional-files/2024-10/2024_gMPI_Table1and2.xlsx'
SHEETS = {'country': ('gMPI_Table1', 6, 131, 171), 'trends': ('Table2', 5, 240, 260)}
MAX_BYTES = 1000000

def query(country, table='country'):
    if not isinstance(country, str) or not 1 <= len(country.strip()) <= 100 or table not in SHEETS:
        raise ValueError('invalid country or table')
    name, header_end, footer_start, footer_end = SHEETS[table]
    response = requests.get(URL, timeout=30, stream=True)
    response.raise_for_status()
    raw = bytearray()
    for block in response.iter_content(65536):
        raw.extend(block)
        if len(raw) > MAX_BYTES:
            raise ValueError('workbook exceeds size limit')
    book = openpyxl.load_workbook(io.BytesIO(raw), read_only=True, data_only=True)
    try:
        sheet = book[name]
        headers, records, notes = ([], [], [])
        for n, row in enumerate(sheet.values, 1):
            if n <= header_end:
                headers.append({'row': n, 'cells': list(row)})
            elif n < footer_start and isinstance(row[0], str) and (row[0].strip().casefold() == country.strip().casefold()):
                if table == 'country':
                    summary = {'survey': row[1], 'survey_note': row[2], 'mpi': row[3], 'mpi_note': row[4], 'headcount_percent': row[5], 'headcount_note': row[6], 'poor_thousands_survey_year': row[7], 'poor_thousands_2022': row[9], 'intensity_percent': row[11]}
                else:
                    summary = {'country_note': row[1], 'survey': row[2], 'survey_note': row[3], 'mpi': row[4], 'mpi_note': row[5], 'headcount_percent': row[6], 'headcount_note': row[7], 'poor_thousands_survey_year': row[8], 'intensity_percent': row[10]}
                summary.update({'row_number': n, 'raw_columns': list(row)})
                records.append(summary)
            elif footer_start <= n <= footer_end and any((v is not None for v in row)):
                notes.append({'row': n, 'cells': list(row)})
            elif n > footer_end:
                break
        return {'source': URL, 'provider': 'UNDP and OPHI', 'edition': '2024 Global MPI', 'sheet': name, 'table': table, 'headers': headers, 'records': records, 'notes': notes, 'note': 'Country survey dates differ; 2022 population projection is not a 2022 survey. Trend estimates are harmonized and can differ from country table. Missing and footnote markers are preserved.'}
    finally:
        book.close()
        response.close()

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('country')
    p.add_argument('--table', choices=SHEETS, default='country')
    a = p.parse_args()
    print(json.dumps(query(a.country, a.table), ensure_ascii=False, indent=2))
if __name__ == '__main__':
    main()
