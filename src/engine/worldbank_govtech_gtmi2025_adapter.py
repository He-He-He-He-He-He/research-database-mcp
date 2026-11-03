"""World Bank GTMI 2025 country group and component scores."""
import release_runtime
import io, re, subprocess
import openpyxl
URL = 'https://datacatalogfiles.worldbank.org/ddh-published/0037889/DR0095721/WBG_GovTech_Dataset_Dec2025.xlsx'
CATALOG = 'https://datacatalog.worldbank.org/search/dataset/0037889/govtech-dataset'

def query(country):
    if not isinstance(country, str) or not re.fullmatch('[A-Za-z]{3}', country):
        raise ValueError('country must be three letters')
    r = release_runtime.run(['/usr/bin/curl', '--fail', '--silent', '--show-error', '--compressed', '--max-time', '60', '--max-filesize', '12000000', URL], capture_output=True, timeout=65)
    if r.returncode:
        raise RuntimeError('download failed: ' + r.stderr.decode('utf-8', 'replace')[:300])
    if len(r.stdout) > 12000000:
        raise ValueError('workbook too large')
    w = openpyxl.load_workbook(io.BytesIO(r.stdout), read_only=True, data_only=True)
    try:
        s = w['GTMI_Groups']
        rows = s.iter_rows(values_only=True)
        h = next(rows)[:13]
        if h != ('Year', 'Code', 'Economy', 'Grp', 'GTMI', 'GT1', 'CGSI', 'GT2', 'PSDI', 'GT3', 'DCEI', 'GT4', 'GTEI'):
            raise ValueError('unexpected workbook layout')
        records = []
        for row in rows:
            if row[0] == 2025 and isinstance(row[1], str) and (row[1].strip().upper() == country.upper()):
                records.append(dict(zip(h, row[:13])))
        return {'source': URL, 'catalog': CATALOG, 'sheet': 'GTMI_Groups', 'columns_returned': list(h), 'records': records, 'note': '2025 GovTech Maturity Index snapshot and four component scores/groups only. Groups A–D are classifications, not ordinal country rankings or a direct measure of effectiveness/readiness. 158 economies self-reported and 39 use remotely collected data; source methods and indicator definitions differ by year. Blank cells remain null. Consult the workbook for indicators, evidence, and methodology. This query does not return all workbook columns.'}
    finally:
        w.close()
