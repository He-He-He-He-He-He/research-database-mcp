"""Crossref metadata for Political Communication, ISSN 1058-4609."""
import release_runtime
import argparse
import json
import requests
URL = 'https://api.crossref.org/journals/1058-4609/works'

def search(keyword, page=1, page_size=10):
    if not isinstance(keyword, str) or not keyword.strip() or len(keyword) > 200:
        raise ValueError('keyword must be 1–200 characters')
    if isinstance(page, bool) or not isinstance(page, int) or (not 1 <= page <= 1000):
        raise ValueError('page must be 1–1000')
    if isinstance(page_size, bool) or not isinstance(page_size, int) or (not 1 <= page_size <= 20):
        raise ValueError('page size must be 1–20')
    if (page - 1) * page_size + page_size > 10000:
        raise ValueError('Crossref offset + rows must not exceed 10000')
    q = keyword.strip()
    r = requests.get(URL, params={'query': q, 'rows': page_size, 'offset': (page - 1) * page_size}, timeout=20)
    r.raise_for_status()
    d = r.json().get('message', {})
    if not isinstance(d.get('items'), list) or not isinstance(d.get('total-results'), int):
        raise ValueError('unexpected Crossref response')
    items = []
    for x in d['items']:
        if '1058-4609' not in x.get('ISSN', []) or not x.get('title'):
            raise ValueError('journal ISSN or title mismatch')
        items.append({'doi': x.get('DOI'), 'title': x['title'][0], 'authors': [{'given': a.get('given'), 'family': a.get('family')} for a in x.get('author', [])], 'type': x.get('type'), 'published': x.get('published', {}).get('date-parts'), 'url': x.get('URL')})
    return {'source': 'Crossref: Political Communication (ISSN 1058-4609)', 'query': q, 'page': page, 'total': d['total-results'], 'items': items, 'source_url': URL, 'note': 'Public Crossref metadata, relevance search, not publisher search; may include non-articles. No evidence of Zhejiang University entitlement or full-text access.'}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('keyword')
    p.add_argument('--page', type=int, default=1)
    p.add_argument('--page-size', type=int, default=10)
    a = p.parse_args()
    print(json.dumps(search(a.keyword, a.page, a.page_size), ensure_ascii=False, indent=2))
if __name__ == '__main__':
    main()
