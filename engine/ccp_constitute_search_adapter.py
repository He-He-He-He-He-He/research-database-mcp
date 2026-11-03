"""Comparative Constitutions Project Constitute public research API."""
import release_runtime
import re
import requests
BASE = 'https://www.constituteproject.org/service/'
TERMS = 'https://www.constituteproject.org/content/terms'

def _get(method, params):
    with requests.get(BASE + method, params=params, timeout=30, stream=True) as r:
        r.raise_for_status()
        raw = bytearray()
        for part in r.iter_content(65536):
            raw.extend(part)
            if len(raw) > 5000000:
                raise ValueError('Response too large')
        import json
        data = json.loads(raw)
        url = r.url
    return (url, data)

def _token(v):
    if not isinstance(v, str) or not re.fullmatch('[A-Za-z0-9_-]{1,100}', v):
        raise ValueError('Invalid country or constitution ID')
    return v

def _language(lang):
    if lang not in ('en', 'es', 'ar'):
        raise ValueError('Language must be en, es or ar')
    return lang

def constitutions(country, language='en'):
    p = {'country': _token(country), 'lang': _language(language)}
    url, data = _get('constitutions', p)
    if not isinstance(data, list):
        raise ValueError('Unexpected response')
    return {'source': url, 'terms': TERMS, 'records': data, 'notes': ['Comparative Constitutions Project research metadata; translations and text may not be official or current.', 'Source in_force, is_historic and update_needed are project metadata, not definitive legal status. Example searches may return more than one version including not-in-force records.', 'Site terms prohibit commercial use; individual translations may have separate rights. Confirm with official legal sources before legal reliance.']}

def search(keyword, country='', constitution='', language='en', limit=20, *, offset=0):
    if not isinstance(keyword, str) or not keyword.strip() or len(keyword) > 100 or any((ord(c) < 32 for c in keyword)) or (type(limit) is not int) or (not 1 <= limit <= 100) or (type(offset) is not int) or (not 0 <= offset <= 100000) or (country and constitution):
        raise ValueError('Invalid query')
    p = {'q': keyword.strip(), 'lang': _language(language)}
    if country:
        p['country'] = _token(country)
    if constitution:
        p['cons_id'] = _token(constitution)
    url, data = _get('textsearch', p)
    if constitution:
        if not isinstance(data, dict):
            raise ValueError('Unexpected section response')
        item = data.get(constitution, {})
        hits = item.get('results', [])
        if not isinstance(hits, list):
            raise ValueError('Unexpected section results')
        total = item.get('num_results')
        result = {'matched_total': total, 'source_items_count': len(hits), 'source_may_be_truncated': total > len(hits) if type(total) is int else None, 'offset': offset, 'limit': limit, 'next_offset': offset + limit if offset + limit < len(hits) else None, 'returned': len(hits[offset:offset + limit]), 'records': hits[offset:offset + limit]}
    else:
        if not isinstance(data, list):
            raise ValueError('Unexpected metadata search response')
        result = {'matched_total': len(data), 'source_items_count': len(data), 'source_may_be_truncated': None, 'offset': offset, 'limit': limit, 'next_offset': offset + limit if offset + limit < len(data) else None, 'returned': len(data[offset:offset + limit]), 'records': data[offset:offset + limit]}
    return dict({'source': url, 'terms': TERMS, 'query': keyword, 'country': country, 'constitution': constitution, 'notes': ['Constitute is a comparative research project, not an official legal registry. Text may be translated, outdated, or subject to third-party rights; confirm effective law with official primary sources.', 'Each request retrieves the source response and slices it locally; source ordering may change. In metadata search the source does not state a total, so completeness is not guaranteed. Matches may include historical or non-effective texts; inspect version and source status. Snippets can contain HTML.', 'Commercial use is prohibited by site terms; personal research should respect attribution and translation rights.']}, **result)
