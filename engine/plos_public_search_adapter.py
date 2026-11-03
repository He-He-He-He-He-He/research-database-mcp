"""One-page bibliographic query via official PLOS Search API."""
import release_runtime
import requests
URL = 'https://api.plos.org/search'

def search(query, offset=0, limit=5, timeout=20):
    if not isinstance(query, str) or not query.strip() or len(query) > 200:
        raise ValueError('query must contain 1–200 characters')
    if isinstance(offset, bool) or not isinstance(offset, int) or (not 0 <= offset <= 5000):
        raise ValueError('offset must be 0–5000')
    if isinstance(limit, bool) or not isinstance(limit, int) or (not 1 <= limit <= 20):
        raise ValueError('limit must be 1–20')
    params = {'q': query.strip(), 'fl': 'id,title,author,journal,publication_date,article_type', 'rows': limit, 'start': offset, 'wt': 'json'}
    r = requests.get(URL, params=params, timeout=timeout)
    r.raise_for_status()
    d = r.json().get('response')
    if not isinstance(d, dict) or not isinstance(d.get('numFound'), int) or (not isinstance(d.get('docs'), list)):
        raise ValueError('unexpected PLOS API response')
    return {'source': 'Public Library of Science Search API', 'query': query.strip(), 'offset': d.get('start'), 'total': d['numFound'], 'items': d['docs'], 'note': 'PLOS 出版物题录；不代表浙大馆藏或全文许可。查询语法由 PLOS Solr 解析。'}
