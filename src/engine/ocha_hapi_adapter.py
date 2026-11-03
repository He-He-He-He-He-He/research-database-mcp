"""UN OCHA HDX HAPI humanitarian indicators and source metadata."""
import release_runtime
import argparse, json, os, re, uuid
from pathlib import Path
import requests
BASE = 'https://hapi.humdata.org/api/v2/'
ENDPOINTS = {'food-security': 'food-security-nutrition-poverty/food-security', 'food-prices': 'food-security-nutrition-poverty/food-prices-market-monitor', 'poverty': 'food-security-nutrition-poverty/poverty-rate', 'rainfall': 'climate/rainfall', 'humanitarian-needs': 'affected-people/humanitarian-needs', 'idps': 'affected-people/idps', 'operational-presence': 'coordination-context/operational-presence', 'funding': 'coordination-context/funding', 'national-risk': 'coordination-context/national-risk'}
MAX = 8 * 1024 * 1024

def _id():
    token = release_runtime.environment.get('HDX_HAPI_IDENTIFIER')
    if token:
        return token
    email = release_runtime.environment.get('HDX_HAPI_EMAIL')
    if not email:
        path = release_runtime.home() / '.config' / 'research-toolkit' / 'hapi-email'
        if path.is_file():
            email = path.read_text(encoding='utf-8').strip()
    if not email:
        raise ValueError('Set HDX_HAPI_IDENTIFIER or HDX_HAPI_EMAIL environment variable')
    try:
        r = requests.get(BASE + 'encode_app_identifier', params={'application': 'ZJU Research Toolkit', 'email': email}, timeout=20)
    except requests.RequestException:
        raise RuntimeError('HAPI identifier endpoint unreachable') from None
    if not r.ok:
        raise RuntimeError('HAPI identifier service failed: HTTP ' + str(r.status_code))
    return r.json()['encoded_app_identifier']

def _get(path, params):
    try:
        with requests.get(BASE + path, params={**params, 'app_identifier': _id()}, timeout=35, stream=True) as r:
            if not r.ok:
                raise RuntimeError('HAPI request failed: HTTP ' + str(r.status_code))
            data = []
            n = 0
            for b in r.iter_content(65536):
                n += len(b)
                if n > MAX:
                    raise ValueError('response exceeds 8 MiB')
                data.append(b)
            obj = json.loads(b''.join(data))
    except requests.RequestException:
        raise RuntimeError('HAPI service unavailable') from None
    return {'source': BASE + path, 'parameters': params, 'result': obj, 'note': '来源、报告期、估计方法及单位须结合资源元数据核验。'}

def data(theme, country, limit=20, offset=0):
    if theme not in ENDPOINTS or not re.fullmatch('[A-Z]{3}', country) or (not 1 <= limit <= 100) or (offset < 0):
        raise ValueError('invalid theme, ISO3 or pagination')
    return _get(ENDPOINTS[theme], {'location_code': country, 'limit': limit, 'offset': offset, 'output_format': 'json'})

def metadata(resource):
    resource = str(uuid.UUID(resource))
    return _get('metadata/resource', {'resource_hdx_id': resource, 'limit': 10, 'output_format': 'json'})

def main():
    p = argparse.ArgumentParser()
    s = p.add_subparsers(dest='cmd', required=True)
    a = s.add_parser('data')
    a.add_argument('theme', choices=ENDPOINTS)
    a.add_argument('country')
    a.add_argument('--limit', type=int, default=20)
    a.add_argument('--offset', type=int, default=0)
    a = s.add_parser('metadata')
    a.add_argument('resource')
    a = p.parse_args()
    x = data(a.theme, a.country, a.limit, a.offset) if a.cmd == 'data' else metadata(a.resource)
    print(json.dumps(x, ensure_ascii=False, indent=2))
if __name__ == '__main__':
    main()
