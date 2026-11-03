"""Read one CLARIN VLO metadata record through the official VLO API."""
import release_runtime
import argparse
import json
import re
import requests
BASE = 'https://vlo.clarin.eu/api/records/'

def detail(identifier):
    if not isinstance(identifier, str) or not re.fullmatch('[A-Za-z0-9_.-]{1,1000}', identifier):
        raise ValueError('invalid VLO record ID')
    r = requests.get(BASE + identifier, timeout=25)
    r.raise_for_status()
    data = r.json()
    if data.get('id') != identifier or not isinstance(data.get('fields'), dict):
        raise ValueError('unexpected VLO response')
    f = data['fields']
    keys = ('name', 'description', 'languageCode', 'resourceClass', 'availability', 'license', 'licenseType', 'organisation', 'country', 'modality')
    return {'source': 'CLARIN Virtual Language Observatory', 'id': identifier, 'metadata_source': data.get('selflink'), 'landingPages': data.get('landingPages'), 'fields': {k: f.get(k) for k in keys}}
if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('identifier')
    print(json.dumps(detail(p.parse_args().identifier), ensure_ascii=False, indent=2))
