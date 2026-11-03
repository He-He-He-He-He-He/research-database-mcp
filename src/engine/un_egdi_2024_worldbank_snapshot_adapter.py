"""UN DESA 2024 EGDI data as reproduced in World Bank GovTech workbook."""
import release_runtime
import io, re, subprocess
import openpyxl
URL = 'https://datacatalogfiles.worldbank.org/ddh-published/0037889/DR0095721/WBG_GovTech_Dataset_Dec2025.xlsx'
CATALOG = 'https://datacatalog.worldbank.org/search/dataset/0037889/govtech-dataset'
METHOD = 'https://desapublications.un.org/sites/default/files/publications/2024-09/Technical%20Appendix%20%28Print%20version%29%201292024.pdf'

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
        rows = w['External'].iter_rows(values_only=True)
        a = next(rows)
        h = next(rows)[:8]
        if a[0] != '2024 UN EGDI' or h[:4] != ('Code', 'Country Name', 'E-Gov Rank', 'E-Gov Index'):
            raise ValueError('unexpected workbook layout')
        out = []
        for row in rows:
            if isinstance(row[0], str) and row[0].strip().upper() == country.upper():
                out.append(dict(zip(h, row[:8])))
        return {'source': URL, 'catalog': CATALOG, 'un_methodology': METHOD, 'edition': 2024, 'sheet': 'External', 'records': out, 'note': 'UN DESA 2024 EGDI as reproduced in the World Bank GTMI workbook, not a direct UN API. Index and components are 0–1 values; E-Gov Rank is a separate ranking. UN survey assesses relative development, not actual service quality or resident adoption. Preserve nulls; compare survey methods across editions and verify original UN data and reuse terms. World Bank copy may lag.'}
    finally:
        w.close()
