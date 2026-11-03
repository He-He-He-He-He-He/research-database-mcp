"""French government public enterprise, association and institution search."""
import release_runtime
import json
import requests
URL = 'https://recherche-entreprises.api.gouv.fr/search'
NOTES = ['French government public business search combines administrative sources including SIRENE and the national business register; it includes associations and public bodies, not only businesses.', 'The API does not cover non-disseminable organisations or the complete underlying SIRENE/RNE registers. Search results and counts can be capped and are not complete population counts.', 'SIREN is a legal-unit identifier; SIRET identifies an establishment. Matching names alone does not establish corporate identity, ownership or financial status.', 'Source records have multiple dates, including employee reference year and update date; preserve them and verify present status. Current data do not reconstruct a historical snapshot.', 'The publisher states maximum seven requests per second per IP and may restrict excessive traffic; honour HTTP 429 and Retry-After.']

def search(query, page=1, limit=10):
    if not isinstance(query, str) or not query.strip() or len(query) > 150 or (type(page) is not int) or (not 1 <= page <= 100) or (type(limit) is not int) or (not 1 <= limit <= 25):
        raise ValueError('Invalid query or pagination')
    with requests.get(URL, params={'q': query, 'page': page, 'per_page': limit}, headers={'User-Agent': 'ZJU-Research-Toolkit/1.0'}, timeout=35, stream=True) as r:
        r.raise_for_status()
        raw = bytearray()
        for c in r.iter_content(65536):
            raw.extend(c)
            if len(raw) > 10000000:
                raise ValueError('response too large')
    j = json.loads(raw)
    if not isinstance(j, dict) or not isinstance(j.get('results'), list):
        raise ValueError('Unexpected search response')
    return {'source': URL, 'query': query, 'notes': NOTES, 'response': j}
