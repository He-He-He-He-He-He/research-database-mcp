"""U.S. National Library of Medicine RxNorm public drug terminology API."""
import release_runtime
import requests
BASE = 'https://rxnav.nlm.nih.gov/REST/'

def _get(path, params=None):
    r = requests.get(BASE + path, params=params, timeout=30)
    r.raise_for_status()
    return r.json()

def version():
    return _get('version.json')

def drugs(name):
    if not name.strip() or len(name) > 200:
        raise ValueError('药名须为 1–200 字符')
    return _get('drugs.json', {'name': name})

def properties(rxcui):
    if not str(rxcui).isdigit() or int(rxcui) < 1:
        raise ValueError('RxCUI 须为正整数')
    return _get('rxcui/' + str(rxcui) + '/allProperties.json', {'prop': 'all'})

def related(rxcui):
    if not str(rxcui).isdigit() or int(rxcui) < 1:
        raise ValueError('RxCUI 须为正整数')
    return _get('rxcui/' + str(rxcui) + '/allrelated.json')
