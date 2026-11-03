"""Unpaywall DOI open-access location lookup (v2)."""
import release_runtime
import os
from urllib.parse import quote
import requests

def lookup(doi, email=None):
    if not isinstance(doi, str) or not doi.lower().startswith('10.') or '/' not in doi:
        raise ValueError('doi must be a bare DOI starting with 10.')
    email = email or release_runtime.getenv('UNPAYWALL_EMAIL')
    if not email or '@' not in email:
        raise ValueError('set UNPAYWALL_EMAIL or pass an email as required by Unpaywall')
    try:
        response = requests.get('https://api.unpaywall.org/v2/' + quote(doi, safe='/'), params={'email': email}, timeout=30)
    except requests.RequestException:
        raise RuntimeError('Unpaywall 网络请求失败') from None
    if not response.ok:
        raise RuntimeError(f'Unpaywall 请求失败: HTTP {response.status_code}')
    data = response.json()
    if not isinstance(data, dict) or 'doi' not in data:
        raise RuntimeError('Unexpected Unpaywall response')
    return {'source': 'Unpaywall', 'data': data, 'note': 'OA status reflects this service and may not cover every lawful version; check license.'}
