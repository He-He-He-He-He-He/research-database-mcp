"""British Geological Survey world minerals OGC Features API."""
import release_runtime
import re
import requests
BASE = 'https://ogcapi.bgs.ac.uk/collections/world-mineral-statistics'
DOC = 'https://www.bgs.ac.uk/mineralsuk/statistics/world-mineral-statistics/world-mineral-statistics-data-download/'
TERMS = 'https://www2.bgs.ac.uk/mineralsUk/statistics/termsAndConditions.html'

def metadata():
    result = {}
    for key, suffix in [('collection', ''), ('queryables', '/queryables')]:
        r = requests.get(BASE + suffix, headers={'Accept': 'application/json'}, timeout=60)
        r.raise_for_status()
        result[key] = r.json()
    return {'source': BASE, 'documentation': DOC, 'data': result}

def observations(country, commodity='', statistic='', offset=0, limit=20):
    if not isinstance(country, str) or not re.fullmatch('[A-Za-z]{3}', country):
        raise ValueError('country must be three alphabetic characters')
    if not isinstance(offset, int) or isinstance(offset, bool) or offset < 0:
        raise ValueError('invalid offset')
    if not isinstance(limit, int) or isinstance(limit, bool) or (not 1 <= limit <= 100):
        raise ValueError('limit must be 1–100')
    if statistic and statistic not in ('Production', 'Imports', 'Exports'):
        raise ValueError('unknown statistic')
    p = {'country_iso3_code': country.upper(), 'offset': offset, 'limit': limit}
    if commodity:
        p['bgs_commodity_trans'] = commodity
    if statistic:
        p['bgs_statistic_type_trans'] = statistic
    r = requests.get(BASE + '/items', params=p, headers={'Accept': 'application/json'}, timeout=60)
    r.raise_for_status()
    j = r.json()
    features = j.get('features')
    if not isinstance(features, list):
        raise ValueError('unexpected feature response')
    for feature in features:
        row = feature.get('properties', {})
        if row.get('country_iso3_code') != country.upper() or (commodity and row.get('bgs_commodity_trans') != commodity) or (statistic and row.get('bgs_statistic_type_trans') != statistic):
            raise ValueError('source ignored or changed requested filter')
    return {'source': BASE + '/items', 'documentation': DOC, 'terms_url': TERMS, 'request': p, 'data': j, 'notes': ['Country, commodity and statistic filters are checked against each returned observation; an empty result cannot establish whether a code or label was valid.', 'Preserve quantity, units, quantity_in_book_style, data_precision_description, SDMX code and footnotes. BGS warns that API zero/NULL alone cannot reliably express all yearbook symbols; do not automatically treat them as zero or non-estimates.', 'Observations may be estimated and have differing commodity definitions and units; the year is the reported statistical year, not the publication date.', 'Trade data from 2003–2018 cover selected European countries only. The linked terms page was unavailable during verification; check reuse conditions with BGS.']}
