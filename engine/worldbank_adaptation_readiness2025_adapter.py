"""World Bank A&R Readiness Assessment country scores, June 2025 workbook."""
import release_runtime
import io, subprocess
import openpyxl
URL = 'https://datacatalogfiles.worldbank.org/ddh-published/0066854/DR0095353/A%26R_Readiness_Assessment_-_external_-_June_12_2025.xlsx'
CATALOG = 'https://datacatalog.worldbank.org/search/dataset/0066854/adaptation-and-resilience-readiness-data'

def query(keyword):
    if not isinstance(keyword, str) or not keyword.strip() or len(keyword) > 100:
        raise ValueError('invalid country keyword')
    r = release_runtime.run(['/usr/bin/curl', '--fail', '--silent', '--show-error', '--compressed', '--max-time', '40', '--max-filesize', '3000000', URL], capture_output=True, timeout=45)
    if r.returncode:
        raise RuntimeError('download failed: ' + r.stderr.decode('utf-8', 'replace')[:300])
    if len(r.stdout) > 3000000:
        raise ValueError('workbook exceeds 3 MB')
    w = openpyxl.load_workbook(io.BytesIO(r.stdout), read_only=True, data_only=True)
    try:
        s = w['country_data']
        rows = s.iter_rows(values_only=True)
        first = next(rows)
        next(rows)
        next(rows)
        next(rows)
        next(rows)
        next(rows)
        h = next(rows)
        if h[0] != 'Pillar' or h[1] != 'ID' or str(h[2]).strip() != 'Indicator':
            raise ValueError('unexpected workbook header')
        idx = [i for i, v in enumerate(h[8:], 8) if isinstance(v, str) and v not in ('hlookup', 'Global average') and (keyword.casefold() in v.casefold())]
        out = [{'country': h[i], 'assessment_fiscal_year': first[i], 'indicators': []} for i in idx]
        for row in rows:
            if row[0] == 'Averages':
                break
            if row[1] not in (None, ''):
                for item, i in zip(out, idx):
                    item['indicators'].append({'pillar': row[0], 'id': row[1], 'indicator': row[2], 'definition': row[3], 'nascent_criteria': row[4], 'emerging_criteria': row[5], 'established_criteria': row[6], 'source_count': row[7], 'score': row[i]})
        return {'source': URL, 'catalog': CATALOG, 'workbook_updated': '2025-06-12', 'sheet': 'country_data', 'records': out, 'note': 'Country scores reflect assessment fiscal years, not necessarily 2025 measurements. Numeric scores classify indicator readiness against criteria, not raw economic or climate observations. Underlying indicators and assessment dates vary by country. Missing values are retained, not zero; a blank score does not prove an action was absent. Match may return multiple countries.'}
    finally:
        w.close()
