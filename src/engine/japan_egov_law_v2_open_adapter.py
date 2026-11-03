"""Japanese Digital Agency e-Gov Law API v2: bounded title search and article."""
import release_runtime
import re
import requests
BASE = 'https://laws.e-gov.go.jp/api/2'
DOC = 'https://laws.e-gov.go.jp/api/2/swagger-ui'

def _get(path, params):
    r = requests.get(BASE + path, params=params, timeout=30)
    r.raise_for_status()
    if len(r.content) > 3000000:
        raise ValueError('Response too large')
    payload = r.json()
    if not isinstance(payload, dict):
        raise ValueError('Unexpected e-Gov JSON response')
    return (r.url, payload)

def search(title, limit=10, offset=0):
    if not isinstance(title, str) or not title.strip() or len(title) > 100:
        raise ValueError('title must be nonempty and at most 100 characters')
    if isinstance(limit, bool) or not isinstance(limit, int) or (not 1 <= limit <= 50):
        raise ValueError('limit must be 1–50')
    if isinstance(offset, bool) or not isinstance(offset, int) or (not 0 <= offset <= 10000):
        raise ValueError('offset must be 0–10000')
    url, data = _get('/laws', {'law_title': title.strip(), 'limit': limit, 'offset': offset})
    if not isinstance(data.get('laws'), list) or not isinstance(data.get('total_count'), int):
        raise ValueError('Unexpected law list response')
    total = data['total_count']
    count = len(data['laws'])
    if total < 0 or count > limit or (offset < total and (not count)):
        raise ValueError('e-Gov page count inconsistent with total')
    return {'source_url': url, 'documentation': DOC, 'offset': offset, 'returned': count, 'next_offset': offset + count if count and offset + count < total else None, 'truncated': offset + count < total, 'data': data, 'note': 'Official Japanese laws; title is partial match. Current and revision information are distinct. Source updates can change cross-page ordering. Not Westlaw Japan content.'}

def article(law_id, article_number):
    if not isinstance(law_id, str) or not re.fullmatch('[0-9]{3}[A-Z]{2}[0-9]{10}', law_id):
        raise ValueError('law_id must be an e-Gov law ID')
    if isinstance(article_number, bool) or not isinstance(article_number, int) or (not 1 <= article_number <= 9999):
        raise ValueError('article_number must be 1–9999')
    params = {'elm': f'Article_{article_number}', 'response_format': 'json', 'law_full_text_format': 'json', 'json_format': 'light'}
    url, data = _get('/law_data/' + law_id, params)
    if not isinstance(data.get('law_info'), dict) or 'law_full_text' not in data:
        raise ValueError('Unexpected law data response')
    return {'source_url': url, 'documentation': DOC, 'data': data, 'note': 'Official e-Gov article response and revision metadata. JSON law body is designated experimental; verify effective dates and official gazette for legal use.'}
