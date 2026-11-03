"""World Bank Global Database on Intergenerational Mobility, March 2023."""
import release_runtime
import csv
import io
import re
import requests
URL = 'https://datacatalogfiles.worldbank.org/ddh-published/0050771/3/DR0065670/GDIM_2023_03.csv'

def query(country_code, *, parent='avg', child='all', limit=50, offset=0):
    if not re.fullmatch('[A-Z]{3}', country_code):
        raise ValueError('country must be ISO3')
    if not all((isinstance(s, str) and re.fullmatch('[A-Za-z0-9_]{1,20}', s) for s in (parent, child))) or type(limit) is not int or (not 1 <= limit <= 100) or (type(offset) is not int) or (offset < 0):
        raise ValueError('invalid parent, child or limit')
    with requests.get(URL, stream=True, timeout=60) as r:
        r.raise_for_status()
        body = r.raw.read(10000001, decode_content=True)
    if len(body) > 10000000:
        raise ValueError('CSV exceeds limit')
    rows = csv.DictReader(io.StringIO(body.decode('utf-8-sig')))
    if not {'code', 'country', 'year', 'cohort', 'parent', 'child', 'obs', 'CAT', 'MEANc'}.issubset(rows.fieldnames or []):
        raise ValueError('unexpected GDIM columns')
    matches = [r for r in rows if r['code'] == country_code and r['parent'] == parent and (r['child'] == child)]
    return {'source': 'World Bank Global Database on Intergenerational Mobility, 2023', 'source_url': URL, 'license': 'CC BY 4.0', 'total_matches': len(matches), 'offset': offset, 'returned': len(matches[offset:offset + limit]), 'next_offset': offset + limit if offset + limit < len(matches) else None, 'truncated': offset + limit < len(matches), 'records': matches[offset:offset + limit], 'note': 'Historical birth cohorts and survey years; CAT is conditional on parents below tertiary education, not the overall mobility rate. Co-residence bias, survey coverage and methodology vary by country. Values are not current measurements. Each request refetches the file; source updates may reorder records across requests.'}
