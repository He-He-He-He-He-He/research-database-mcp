"""NCBI E-utilities multi-database search and summaries (read only)."""
import release_runtime
import os
import requests
_BASE = 'https://eutils.ncbi.nlm.nih.gov/entrez/eutils/'

def _get(endpoint, params):
    params = dict(params, retmode='json', tool='personal_research_cli')
    if release_runtime.getenv('NCBI_EMAIL'):
        params['email'] = release_runtime.environment['NCBI_EMAIL']
    if release_runtime.getenv('NCBI_API_KEY'):
        params['api_key'] = release_runtime.environment['NCBI_API_KEY']
    try:
        response = requests.get(_BASE + endpoint + '.fcgi', params=params, timeout=30)
    except requests.RequestException:
        raise RuntimeError('NCBI E-utilities 网络请求失败') from None
    if not response.ok:
        raise RuntimeError(f'NCBI E-utilities 请求失败: HTTP {response.status_code}')
    result = response.json()
    if 'error' in result:
        raise RuntimeError(str(result['error']))
    return result

def databases():
    return _get('einfo', {})['einforesult']['dblist']

def search(database, query, size=10, start=0):
    if not isinstance(database, str) or not database.strip() or (not isinstance(query, str)) or (not query.strip()):
        raise ValueError('database and query must be non-empty strings')
    if not isinstance(size, int) or isinstance(size, bool) or (not 1 <= size <= 100):
        raise ValueError('size must be between 1 and 100')
    if not isinstance(start, int) or isinstance(start, bool) or start < 0:
        raise ValueError('start must be a non-negative integer')
    data = _get('esearch', {'db': database, 'term': query, 'retmax': size, 'retstart': start})
    result = data['esearchresult']
    if result.get('errorlist'):
        raise RuntimeError(str(result['errorlist']))
    return {'source': 'NCBI Entrez', 'database': database, 'query': query, 'total': int(result['count']), 'ids': result['idlist'], 'query_translation': result.get('querytranslation'), 'start': start}

def summaries(database, ids):
    if not isinstance(database, str) or not database.strip():
        raise ValueError('database must be a non-empty string')
    if not isinstance(ids, (list, tuple)) or not ids or len(ids) > 100 or (not all((str(i).isdigit() for i in ids))):
        raise ValueError('ids must be 1 to 100 numeric identifiers')
    return _get('esummary', {'db': database, 'id': ','.join(map(str, ids))})['result']
