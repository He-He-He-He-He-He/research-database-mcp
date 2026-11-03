"""Norwegian Brønnøysund public legal-entity register."""
import release_runtime
import json
import re
import requests
BASE = 'https://data.brreg.no/enhetsregisteret/api/enheter'
NOTES = ['Official Norwegian Central Coordinating Register for Legal Entities, including businesses and other legal entities; search results are not limited to companies.', 'Registration or a bankruptcy flag alone does not establish operational status, regulatory authorisation, financial health, ownership or beneficial owners.', 'Source employee numbers and company details may have their own reporting dates; preserve original fields and verify updates.', 'The current register is not a historical snapshot. Public data are subject to the Norwegian Licence for Open Government Data (NLOD); source attribution and other conditions apply.']

def _get(url, params=None):
    with requests.get(url, params=params, timeout=40, stream=True) as r:
        r.raise_for_status()
        raw = bytearray()
        for c in r.iter_content(65536):
            raw.extend(c)
            if len(raw) > 10000000:
                raise ValueError('response exceeds size limit')
    j = json.loads(raw)
    if not isinstance(j, dict):
        raise ValueError('Unexpected register response')
    return j

def search(name, page=0, size=10):
    if not isinstance(name, str) or not name.strip() or len(name) > 100 or (type(page) is not int) or (not 0 <= page <= 1000) or (type(size) is not int) or (not 1 <= size <= 50):
        raise ValueError('Invalid search')
    j = _get(BASE, {'navn': name, 'page': page, 'size': size})
    p = j.get('page')
    e = j.get('_embedded', {})
    if not isinstance(p, dict) or not isinstance(e, dict) or ('enheter' in e and (not isinstance(e['enheter'], list))):
        raise ValueError('Unexpected search response')
    return {'source': BASE, 'query': name, 'notes': NOTES, 'response': j}

def entity(orgnr):
    if not isinstance(orgnr, str) or not re.fullmatch('\\d{9}', orgnr):
        raise ValueError('Organisation number must be nine digits')
    url = BASE + '/' + orgnr
    j = _get(url)
    if j.get('organisasjonsnummer') != orgnr:
        raise ValueError('Unexpected entity')
    return {'source': url, 'notes': NOTES, 'entity': j}
