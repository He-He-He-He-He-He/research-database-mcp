"""ITU's public ICT Development Index 2024 edition workbook."""
import release_runtime
import hashlib
import io
import re
import requests
import openpyxl
PAGE = 'https://www.itu.int/itu-d/reports/statistics/idi2024/'
URL = 'https://www.itu.int/itu-d/reports/statistics/wp-content/uploads/sites/5/2026/05/IDIDataset2024edition.xlsx'
NOTES = ['This is the 2024 edition workbook currently distributed by ITU at a path containing 2026/05; do not assume these exact bytes were available before a historical cutoff.', 'Indicator values generally refer to 2022; ‡ denotes a 2021 lagged value, and source descriptions identify estimates. Preserve symbols, n.a., n.p., blanks and original source fields.', 'Indicators, normalised scores, pillars and the overall index are different measures; do not treat scores as percentages.', 'The original workbook uses merged multilevel column headers; all original header rows, cells and indicator definitions are returned. Consult the original report for methods and usage conditions.']

def query(iso3):
    if not isinstance(iso3, str) or not re.fullmatch('[A-Za-z]{3}', iso3):
        raise ValueError('ISO3 must contain three letters')
    iso3 = iso3.upper()
    r = requests.get(URL, timeout=60)
    r.raise_for_status()
    if not r.content.startswith(b'PK'):
        raise ValueError('ITU did not return an XLSX file')
    w = openpyxl.load_workbook(io.BytesIO(r.content), data_only=True, read_only=False)
    if 'IDI 2024 Data' not in w.sheetnames or 'Definitions' not in w.sheetnames:
        raise ValueError('Unexpected workbook layout')
    s = w['IDI 2024 Data']
    if s.cell(5, 1).value != 'Iso3' or s.cell(5, 4).value != 'Economy' or s.cell(5, 5).value != 'Individuals using the Internet (%)' or (s.cell(5, 38).value != 'ICT Development Index (IDI)'):
        raise ValueError('Unexpected ITU headers')
    rows = []
    for row in s.iter_rows(min_row=7, values_only=True):
        if row[0] == iso3:
            rows.append(list(row))
    if len(rows) > 1:
        raise ValueError('Duplicate country code in ITU workbook')
    definitions = [list(row) for row in w['Definitions'].iter_rows(values_only=True)]
    return {'source': URL, 'report_page': PAGE, 'file_sha256': hashlib.sha256(r.content).hexdigest(), 'worksheet': s.title, 'header_rows_1_to_6': [list(row) for row in s.iter_rows(min_row=1, max_row=6, values_only=True)], 'merged_header_ranges': [str(m) for m in s.merged_cells.ranges if m.min_row <= 6], 'rows': rows, 'footer_notes': [s.cell(i, 5).value for i in range(7, s.max_row + 1) if isinstance(s.cell(i, 5).value, str) and (s.cell(i, 5).value.startswith('Note:') or s.cell(i, 5).value.startswith('Source:') or s.cell(i, 5).value.startswith('For details'))], 'definitions': definitions, 'notes': NOTES}
