"""ITU Global Cybersecurity Index score series from World Bank Data360."""
import release_runtime
import re
import requests
URL = 'https://data360api.worldbank.org/data360/data'
DATASET = 'ITU_GCI'
INDICATORS = {'overall': ('ITU_GCI_GCI_OVRL_SCRE', '0_TO_100'), 'legal': ('ITU_GCI_LEGL_SCRE', '0_TO_20'), 'technical': ('ITU_GCI_TECH_SCORE', '0_TO_20'), 'organizational': ('ITU_GCI_ORG_SCORE', '0_TO_20'), 'capacity': ('ITU_GCI_CDS_SCORE', '0_TO_20'), 'cooperation': ('ITU_GCI_COOP_SCORE', '0_TO_20')}
DOC = 'https://www.itu.int/dms_pub/itu-d/opb/hdb/d-hdb-gci.01-2024-pdf-e.pdf'

def query(country, kind, start, end):
    if not isinstance(country, str) or not re.fullmatch('[A-Za-z]{3}', country):
        raise ValueError('country must be ISO3')
    if kind not in INDICATORS:
        raise ValueError('unknown kind')
    if any((not isinstance(x, int) or isinstance(x, bool) for x in (start, end))) or not 1900 <= start <= end <= 2100:
        raise ValueError('invalid year range')
    indicator, unit = INDICATORS[kind]
    p = {'DATABASE_ID': DATASET, 'INDICATOR': indicator, 'REF_AREA': country.upper(), 'timePeriodFrom': start, 'timePeriodTo': end}
    r = requests.get(URL, params=p, timeout=45)
    r.raise_for_status()
    j = r.json()
    rows = j.get('value')
    if not isinstance(rows, list) or not isinstance(j.get('count'), int) or j['count'] != len(rows):
        raise ValueError('incomplete or unexpected response')
    if any((x.get('DATABASE_ID') != DATASET or x.get('INDICATOR') != indicator or x.get('REF_AREA') != country.upper() or (x.get('UNIT_MEASURE') != unit) or (x.get('UNIT_MULT') != 0) for x in rows)):
        raise ValueError('unexpected dimensions or scale')
    return {'source': URL, 'request': p, 'metadata': 'https://data360files.worldbank.org/data360-data/metadata/ITU_GCI/' + indicator + '.pdf', 'itu_report': DOC, 'kind': kind, 'source_unit': unit, 'data': rows, 'notes': ['ITU global cybersecurity commitment index, transmitted through World Bank Data360; it is a survey-based policy/capacity score, not observed cybercrime prevalence or breach probability.', 'Overall score range is 0–100; each pillar is 0–20. These are index points, not percentages or rankings.', 'The 2024 report methodology and country participation must be checked before comparing years. Missing years are not zero; the Data360 copy may lag.', 'ITU 2024 report states CC BY-NC-SA 3.0 IGO; World Bank reproducibility metadata says CC BY-NC 3.0 IGO for its consolidated panel. Verify terms before redistribution and commercial use.']}
