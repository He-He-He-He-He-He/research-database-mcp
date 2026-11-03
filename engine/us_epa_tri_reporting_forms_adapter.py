"""US EPA TRI reporting form, facility and chemical records."""
import release_runtime
import re
import requests
BASE = 'https://data.epa.gov/efservice/'
DOC = 'https://www.epa.gov/enviro/envirofacts-data-service-api'
KEEP = ('tri_facility_id', 'facility_name', 'street_address', 'city_name', 'county_name', 'state_abbr', 'zip_code', 'epa_registry_id', 'doc_ctrl_num', 'active_status', 'reporting_year', 'form_type_ind', 'tri_chem_id', 'cas_chem_name', 'chem_name', 'cas_registry_number', 'unit_of_measure', 'max_amount_of_chem', 'one_time_release_qty', 'one_time_release_qty_na', 'one_time_release_qty_air', 'one_time_release_qty_water', 'one_time_release_qty_land', 'one_time_release_qty_offsite', 'production_ratio', 'production_ratio_na', 'received_date', 'revision_na', 'carc_ind', 'pbt_ind', 'pfas_ind')

def forms(state, year, offset=0, limit=10):
    if not isinstance(state, str) or not re.fullmatch('[A-Z]{2}', state):
        raise ValueError('state must be two uppercase letters')
    if type(year) is not int or not 1987 <= year <= 2100 or type(offset) is not int or (not 0 <= offset <= 1000000) or (type(limit) is not int) or (not 1 <= limit <= 25):
        raise ValueError('Invalid year or pagination')
    path = f'tri_facility/state_abbr/{state}/tri_reporting_form/reporting_year/{year}/tri_chem_info/rows/{offset}:{offset + limit - 1}/JSON'
    r = requests.get(BASE + path, timeout=40)
    r.raise_for_status()
    j = r.json()
    if not isinstance(j, list):
        raise ValueError('Unexpected EPA response')
    if any((str(x.get('reporting_year')) != str(year) or x.get('state_abbr') != state for x in j)):
        raise ValueError('EPA response does not match filters')
    return {'source': r.url, 'documentation': DOC, 'state': state, 'reporting_year': year, 'offset': offset, 'requested': limit, 'returned': len(j), 'records': [{k: x[k] for k in KEEP if k in x} for x in j], 'notes': ['Rows are TRI facility reporting forms joined with chemical metadata, not an aggregate release total. Selected fields are returned; contact information is omitted.', 'EPA TRI covers specified facilities and chemicals; it is not all releases or direct evidence of human exposure or health risk.', 'Read unit_of_measure per chemical: EPA notes dioxin quantities use grams while most chemicals use pounds. NA markers and nulls are not zero.', 'One-time release fields are not total annual releases. Reporting year, receipt date, active status and revision indicators have distinct meanings.', 'Source does not supply total count or guaranteed ordering here; a page is not necessarily exhaustive, and records can be revised.']}
