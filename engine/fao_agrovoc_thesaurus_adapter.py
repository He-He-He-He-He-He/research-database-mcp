"""FAO AGROVOC public multilingual thesaurus; not a document database."""
import release_runtime
import argparse
import json
import requests
URL = 'https://agrovoc.fao.org/browse/rest/v1/search/'

def search(term, language='en', limit=10):
    if not isinstance(term, str) or not term.strip() or len(term) > 120:
        raise ValueError('term must be 1–120 characters')
    if language not in ('en', 'zh', 'ar', 'fr', 'ru', 'es'):
        raise ValueError('language must be en, zh, ar, fr, ru or es')
    if not isinstance(limit, int) or not 1 <= limit <= 20:
        raise ValueError('limit must be between 1 and 20')
    if '*' in term or '?' in term:
        raise ValueError('wildcards are not accepted; search uses prefix matching')
    response = requests.get(URL, params={'query': term.strip() + '*', 'lang': language, 'maxhits': limit}, timeout=20)
    response.raise_for_status()
    data = response.json()
    if not isinstance(data.get('results'), list):
        raise ValueError('Unexpected AGROVOC response')
    return {'source': 'FAO AGROVOC', 'query': term.strip(), 'language': language, 'limit': limit, 'returned': min(len(data['results']), limit), 'possibly_truncated': len(data['results']) >= limit, 'results': data['results'][:limit], 'note': 'Source does not provide a total; when possibly_truncated is true more matches may exist; false does not prove completeness. Increase limit up to 20 or narrow the prefix; this is a thesaurus, not a document database.'}
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('term')
    parser.add_argument('--language', default='en')
    parser.add_argument('--limit', type=int, default=10)
    args = parser.parse_args()
    print(json.dumps(search(args.term, args.language, args.limit), ensure_ascii=False, indent=2))
