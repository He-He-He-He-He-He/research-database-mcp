"""NCBI PMC article identifier converter; only articles in PMC are covered."""
import release_runtime
import os
import requests

def convert(ids, idtype=None, email=None):
    if not isinstance(ids, (list, tuple)) or not 1 <= len(ids) <= 200:
        raise ValueError('ids must be a list of 1 to 200 identifiers of the same type')
    if not all((isinstance(x, str) and x.strip() and (',' not in x) for x in ids)):
        raise ValueError('identifiers must be non-empty strings without commas')
    if idtype is not None and idtype not in ('pmid', 'pmcid', 'doi', 'mid'):
        raise ValueError('idtype must be pmid, pmcid, doi or mid')
    email = email or release_runtime.getenv('NCBI_EMAIL')
    if not email or '@' not in email:
        raise ValueError('NCBI requests a maintainer email; set NCBI_EMAIL or pass email')
    params = {'ids': ','.join(ids), 'format': 'json', 'tool': 'personal_research_cli', 'email': email}
    if idtype:
        params['idtype'] = idtype
    try:
        r = requests.get('https://pmc.ncbi.nlm.nih.gov/tools/idconv/api/v1/articles/', params=params, timeout=30)
    except requests.RequestException:
        raise RuntimeError('PMC ID conversion request failed') from None
    if not r.ok:
        raise RuntimeError(f'PMC ID conversion returned HTTP {r.status_code}')
    data = r.json()
    if data.get('status') != 'ok' or not isinstance(data.get('records'), list):
        raise RuntimeError('PMC ID conversion failed: ' + str(data.get('errmsg', data.get('status'))))
    return {'source': 'NCBI PMC ID Converter', 'idtype': idtype, 'records': data['records'], 'note': 'Only articles in PMC have mappings; missing mappings do not prove nonexistence elsewhere.'}
