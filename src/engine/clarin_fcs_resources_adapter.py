"""Find resources in CLARIN's public Federated Content Search directory."""
import release_runtime
import argparse
import json
import requests
URL = 'https://contentsearch.clarin.eu/rest/resources'

def search(query, language=None, limit=10, *, offset=0):
    if not isinstance(query, str) or not query.strip() or len(query) > 100:
        raise ValueError('query must be 1–100 characters')
    if language is not None and (not isinstance(language, str) or not language.isalpha() or len(language) != 3):
        raise ValueError('language must be a 3-letter code')
    if not isinstance(limit, int) or not 1 <= limit <= 20:
        raise ValueError('limit must be 1–20')
    if type(offset) is not int or offset < 0:
        raise ValueError('offset must be a nonnegative integer')
    r = requests.get(URL, timeout=25)
    r.raise_for_status()
    data = r.json()
    if not isinstance(data, list):
        raise ValueError('unexpected FCS resource response')
    q = query.strip().casefold()
    found = []
    for row in data:
        title = row.get('title') or {}
        institution = row.get('institution') or {}
        if q not in json.dumps([title, institution], ensure_ascii=False).casefold():
            continue
        if language and language.lower() not in [str(v).lower() for v in row.get('languages') or []]:
            continue
        found.append({'id': row.get('id'), 'title': title, 'institution': institution, 'languages': row.get('languages'), 'availabilityRestriction': row.get('availabilityRestriction'), 'landingPage': row.get('landingPage'), 'handle': row.get('handle'), 'searchCapabilities': row.get('searchCapabilities')})
    return {'source': 'CLARIN Federated Content Search resource directory', 'source_url': URL, 'directory_size': len(data), 'matching': len(found), 'offset': offset, 'returned': len(found[offset:offset + limit]), 'next_offset': offset + limit if offset + limit < len(found) else None, 'truncated': offset + limit < len(found), 'results': found[offset:offset + limit], 'note': 'Directory is fetched anew each request; updates may change ordering. Resource entries do not establish full-text access.'}
if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('query')
    p.add_argument('--language')
    p.add_argument('--limit', type=int, default=10)
    p.add_argument('--offset', type=int, default=0)
    a = p.parse_args()
    print(json.dumps(search(a.query, a.language, a.limit, offset=a.offset), ensure_ascii=False, indent=2))
