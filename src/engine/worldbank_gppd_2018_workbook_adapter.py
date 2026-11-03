"""World Bank historical GPPD workbook, as published in 2021."""
import release_runtime
import io, re, subprocess
import openpyxl
URL = 'https://datacatalogfiles.worldbank.org/ddh-published/0038958/1/DR0048292/gov_global_public_procurement.xlsx'
CATALOG = 'https://datacatalog.worldbank.org/search/dataset/0038958/global-public-procurement-database'

def query(country):
    if not isinstance(country, str) or not re.fullmatch('[A-Za-z]{3}', country):
        raise ValueError('country must be a three-letter code')
    r = release_runtime.run(['/usr/bin/curl', '--fail', '--silent', '--show-error', '--compressed', '--max-time', '40', '--max-filesize', '3000000', URL], capture_output=True, timeout=45)
    if r.returncode:
        raise RuntimeError('download failed: ' + r.stderr.decode('utf-8', 'replace')[:300])
    if len(r.stdout) > 3000000:
        raise ValueError('workbook exceeds 3 MB')
    w = openpyxl.load_workbook(io.BytesIO(r.stdout), read_only=True, data_only=True)
    try:
        rows = w.active.iter_rows(values_only=True)
        h = next(rows)
        if h[:5] != ('Country', 'Country ISO3', 'Region', 'Population', 'Year'):
            raise ValueError('unexpected headers')
        out = []
        for row in rows:
            if isinstance(row[1], str) and row[1].upper() == country.upper():
                out.append({'columns': h, 'values': row})
        return {'source': URL, 'catalog': CATALOG, 'country': country.upper(), 'records': out, 'note': 'Historical workbook published 2021; row Year is not necessarily the reference date for every field. It is not current law or a procurement contract database. Empty cells remain null. Known source inconsistency: Egypt row lists base currency as Yemeni Rial while supported currencies list Egyptian Pound; preserve both and verify against primary sources.'}
    finally:
        w.close()
