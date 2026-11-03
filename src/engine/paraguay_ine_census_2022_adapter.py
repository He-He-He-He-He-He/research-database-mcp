"""INE Paraguay 2022 final census population by department."""
import release_runtime
import hashlib
import re
import requests
from bs4 import BeautifulSoup
URL = 'https://www.ine.gov.py/noticias/2101/principales-'
P = re.compile('^(.+?) total ([\\d.]+)[;:]\\s*([\\d.]+) hombres[;,]\\s*([\\d.]+) mujeres$', re.I)
NOTES = ['This is the 2022 census final count reported by INE in August 2024, not a current population estimate or projected population.', 'Asunción and departments form the source categories. Preserve source names; national and department totals overlap and should not be added together.', 'The numeric values are parsed from Spanish thousands-separated source text and validated against source national totals. Retain the original text for audit.', 'Census totals and population estimates may differ due to coverage and methodology. Consult official documentation before comparing.']

def query(keyword=''):
    if not isinstance(keyword, str) or len(keyword) > 100:
        raise ValueError('Invalid keyword')
    r = requests.get(URL, timeout=45)
    r.raise_for_status()
    s = BeautifulSoup(r.text, 'html.parser')
    rows = []
    for line in s.stripped_strings:
        m = P.fullmatch(line)
        if not m:
            continue
        nums = [int(v.replace('.', '')) for v in m.groups()[1:]]
        if nums[0] != nums[1] + nums[2]:
            raise ValueError('INE category arithmetic mismatch')
        rows.append({'geography_raw': m[1], 'total': nums[0], 'men': nums[1], 'women': nums[2], 'source_text': line})
    if len(rows) != 18 or len({r['geography_raw'] for r in rows}) != 18:
        raise ValueError('INE census department list incomplete')
    full = s.get_text(' ', strip=True)
    if not all((v in full for v in ('6.109.903', '3.057.674', '3.052.229'))) or tuple((sum((x[k] for x in rows)) for k in ('total', 'men', 'women'))) != (6109903, 3057674, 3052229):
        raise ValueError('INE national cross-check failed')
    return {'source': URL, 'census_year': 2022, 'census_day': '2022-11-09', 'census_day_source': 'https://www.bacn.gov.py/leyes-paraguayas/10794/ley-n-6987-dispone-la-fecha-de-realizacion-del-censo-nacional-de-poblacion-y-viviendas-del-ano-2022', 'unit': 'persons', 'source_publication_date': '2024-08-21', 'sha256': hashlib.sha256(r.content).hexdigest(), 'national_totals_source': {'total': 6109903, 'men': 3057674, 'women': 3052229}, 'total_matching': sum((keyword.casefold() in x['geography_raw'].casefold() for x in rows)), 'notes': NOTES, 'records': [x for x in rows if keyword.casefold() in x['geography_raw'].casefold()]}
