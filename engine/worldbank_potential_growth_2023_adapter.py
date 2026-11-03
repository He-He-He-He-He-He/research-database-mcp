"""World Bank March 2023 cross-country potential growth model estimates."""
import release_runtime
import io, re, subprocess
import openpyxl
URL = 'https://datacatalogfiles.worldbank.org/ddh-published/0065153/DR0092743/Potential-growth-database.xlsx'
CATALOG = 'https://datacatalog.worldbank.org/search/dataset/0065153/a-cross-country-database-of-potential-growth'

def query(country, start, end):
    if not isinstance(country, str) or not re.fullmatch('[A-Za-z]{3}', country):
        raise ValueError('country must be three letters')
    if any((isinstance(x, bool) or not isinstance(x, int) for x in (start, end))) or not 1981 <= start <= end <= 2021:
        raise ValueError('years must be 1981–2021')
    r = release_runtime.run(['/usr/bin/curl', '--fail', '--silent', '--show-error', '--compressed', '--max-time', '40', '--max-filesize', '4000000', URL], capture_output=True, timeout=45)
    if r.returncode:
        raise RuntimeError('download failed: ' + r.stderr.decode('utf-8', 'replace')[:300])
    if len(r.stdout) > 4000000:
        raise ValueError('workbook too large')
    w = openpyxl.load_workbook(io.BytesIO(r.stdout), read_only=True, data_only=True)
    try:
        rows = w['PotentialGrowthMeasures'].iter_rows(values_only=True)
        h = next(rows)
        if h[:4] != ('IFS code', 'ISO3 code', 'Country', 'Year'):
            raise ValueError('unexpected workbook header')
        out = []
        for row in rows:
            if isinstance(row[1], str) and row[1].upper() == country.upper() and isinstance(row[3], int) and (start <= row[3] <= end):
                out.append({'columns': h, 'values': row})
        return {'source': URL, 'catalog': CATALOG, 'workbook_version': 'March 2023', 'records': out, 'note': 'Model-based historical estimates of potential growth, not actual GDP growth or a guaranteed forecast. Different filter and production-function methods may yield different values; five-year-ahead IMF WEO expectation is a separate measure. Rate fields are percent; capital and labor contribution fields are percentage points. Null remains missing. Catalog file update is March 2025, whereas workbook itself states March 2023 version.'}
    finally:
        w.close()
