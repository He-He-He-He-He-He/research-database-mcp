"""FDA Orange Book drug product, patent and exclusivity API."""
import release_runtime
import re
import requests
URL = 'https://api.fda.gov/drug/orangebook.json'
DOC = 'https://open.fda.gov/apis/drug/orangebook/'
FIELDS = {'ingredient': 'products.active_ingredients.name', 'brand': 'products.brand_name', 'application': 'products.application_number'}

def search(field, term, limit=20, offset=0):
    if field not in FIELDS or not isinstance(term, str) or (not re.fullmatch("[A-Za-z0-9 .,'+\\-]{1,100}", term)) or (not term.strip()):
        raise ValueError('Invalid field or query term')
    if field == 'application' and (not re.fullmatch('\\d{6}', term)):
        raise ValueError('FDA application number must contain six digits')
    if type(limit) is not int or not 1 <= limit <= 99 or type(offset) is not int or (not 0 <= offset <= 25000):
        raise ValueError('Invalid pagination')
    p = {'search': FIELDS[field] + ':"' + term.strip() + '"', 'limit': limit, 'skip': offset}
    r = requests.get(URL, params=p, timeout=30)
    if r.status_code == 404:
        j = r.json()
        if j.get('error', {}).get('code') == 'NOT_FOUND':
            return {'source': r.url, 'documentation': DOC, 'matched_total': 0, 'returned': 0, 'records': [], 'notes': ['No results for this query, not proof that the product is unapproved or unlisted.']}
    r.raise_for_status()
    j = r.json()
    if not isinstance(j.get('results'), list) or 'results' not in j.get('meta', {}):
        raise ValueError('Unexpected FDA response')
    return {'source': r.url, 'documentation': DOC, 'fda_meta': j['meta'], 'matched_total': j['meta']['results']['total'], 'returned': len(j['results']), 'records': j['results'], 'notes': ['Orange Book is an FDA dataset of approved drug products and associated listed patent and exclusivity information; it is not a complete patent registry.', 'Patent listing or a listed expiration date does not by itself establish current patent validity, enforceability, or freedom to operate; marketing status must be read per product.', 'Search is FDA indexed phrase matching, not guaranteed exact identity. Different strengths, application types and discontinued products may appear.', 'Current FDA data can be updated or corrected. Results are not individual medical advice and should be verified against FDA original records.']}
