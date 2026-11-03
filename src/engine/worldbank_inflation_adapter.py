"""World Bank cross-country inflation workbook (annual sheets only)."""
import release_runtime
import io, re, subprocess
import openpyxl
URL = 'https://thedocs.worldbank.org/en/doc/1ad246272dbbc437c74323719506aa0c-0350012021/original/Inflation-data.xlsx'
CATALOG = 'https://datacatalog.worldbank.org/search/dataset/0065307/inflation-in-emerging-and-developing-economies'
SHEETS = {'headline': 'hcpi_a', 'food': 'fcpi_a', 'energy': 'ecpi_a', 'core': 'ccpi_a', 'producer': 'ppi_a', 'gdp-deflator': 'def_a'}

def query(country, metric, start, end):
    if not isinstance(country, str) or not re.fullmatch('[A-Za-z]{3}', country):
        raise ValueError('invalid country code')
    if metric not in SHEETS:
        raise ValueError('invalid metric')
    if any((isinstance(x, bool) or not isinstance(x, int) or (not 1900 <= x <= 2100) for x in (start, end))) or start > end:
        raise ValueError('invalid years')
    r = release_runtime.run(['/usr/bin/curl', '--fail', '--silent', '--show-error', '--compressed', '--max-time', '60', '--max-filesize', '15000000', URL], capture_output=True, timeout=65)
    if r.returncode:
        raise RuntimeError('download failed: ' + r.stderr.decode('utf-8', 'replace')[:300])
    if len(r.stdout) > 15000000:
        raise ValueError('workbook exceeds 15 MB')
    wb = openpyxl.load_workbook(io.BytesIO(r.stdout), read_only=True, data_only=True)
    try:
        intro = [[v for v in row if v is not None] for row in wb['Intro'].iter_rows(values_only=True)]
        version = next((x[0] for x in intro if len(x) == 1 and str(x[0]).startswith('Version:')), None)
        sheet = wb[SHEETS[metric]]
        rows = sheet.iter_rows(values_only=True)
        h = next(rows)
        if h[0] != 'Country Code' or h[3] != 'Indicator Type':
            raise ValueError('unexpected workbook layout')
        out = []
        for row in rows:
            if row[0] == country.upper():
                metadata = [{'column': i + 1, 'header': h[i], 'value': row[i]} for i in range(len(h)) if not isinstance(h[i], int) and (h[i] is not None or row[i] is not None)]
                values = [{'column': i + 1, 'year': v, 'value': row[i]} for i, v in enumerate(h) if isinstance(v, int) and (not isinstance(v, bool)) and (start <= v <= end)]
                out.append({'metadata': metadata, 'values': values})
        return {'source': URL, 'catalog': CATALOG, 'workbook_version': version, 'sheet': SHEETS[metric], 'country': country.upper(), 'records': out, 'note': 'Annual inflation rates are percentage changes of annual averages unless otherwise specified. Source notes and missing cells are retained. GDP-deflator growth is distinct from CPI inflation. The workbook version and the catalog temporal coverage may disagree; consult the source for revisions and latest available year.'}
    finally:
        wb.close()
