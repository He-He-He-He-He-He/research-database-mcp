"""US EIA CBECS 2018 C1 official table: energy use and relative standard errors."""
import release_runtime
import io
import requests
import openpyxl
URL = 'https://www.eia.gov/consumption/commercial/data/2018/ce/xls/c1.xlsx'
PAGE = 'https://www.eia.gov/consumption/commercial/data/2018/index.php?view=consumption'

def _load():
    r = requests.get(URL, timeout=35)
    r.raise_for_status()
    if len(r.content) > 5000000:
        raise ValueError('workbook too large')
    w = openpyxl.load_workbook(io.BytesIO(r.content), data_only=True)
    if not {'data', 'rse'}.issubset(w.sheetnames):
        raise ValueError('unexpected workbook sheets')
    return w

def search(keyword, limit=20, offset=0):
    if not isinstance(keyword, str) or not keyword.strip() or len(keyword) > 120:
        raise ValueError('invalid keyword')
    if any((isinstance(x, bool) or not isinstance(x, int) for x in (limit, offset))) or not 1 <= limit <= 100 or offset < 0:
        raise ValueError('invalid pagination')
    w = _load()
    s = w['data']
    r = w['rse']
    if 'Table C1.' not in str(s.cell(2, 1).value) or '2018' not in str(s.cell(2, 1).value):
        raise ValueError('unexpected C1 workbook')
    matches = []
    heading = None
    for i in range(6, s.max_row + 1):
        name = s.cell(i, 1).value
        if not isinstance(name, str) or not name.strip():
            continue
        values = [s.cell(i, j).value for j in range(2, 10)]
        if all((v is None or (isinstance(v, str) and (not v.strip())) for v in values)):
            heading = name
            continue
        if keyword.casefold() in name.casefold():
            if str(r.cell(i, 1).value).strip() != name.strip():
                raise ValueError('RSE row misalignment')
            matches.append({'row_number': i, 'section': heading, 'label': name, 'indent': s.cell(i, 1).alignment.indent, 'values': values, 'rse_values': [r.cell(i, j).value for j in range(2, 10)]})
    notes = [str(s.cell(i, 1).value) for i in range(6, s.max_row + 1) if isinstance(s.cell(i, 1).value, str) and s.cell(i, 1).value.startswith('Data source:')]
    return {'source': URL, 'documentation': PAGE, 'survey_year': 2018, 'release': 'Revised December 2022', 'columns': ['buildings_thousands', 'floorspace_million_sq_ft', 'major_fuels_trillion_btu', 'electricity_primary_trillion_btu', 'electricity_site_trillion_btu', 'natural_gas_trillion_btu', 'fuel_oil_trillion_btu', 'district_heat_trillion_btu'], 'source_header_rows': [[s.cell(i, j).value for j in range(1, 10)] for i in range(3, 6)], 'matched': len(matches), 'offset': offset, 'limit': limit, 'rows': matches[offset:offset + limit], 'source_notes': notes, 'note': '2018 US commercial building survey estimates, not current or Egypt-specific building data. RSE values are relative standard errors; Q and blanks must not be treated as zero. Primary electricity is an alternative basis to site electricity and cannot be added to major-fuel sum; category subtotals can overlap. Preserve source row hierarchy and footnotes.'}
