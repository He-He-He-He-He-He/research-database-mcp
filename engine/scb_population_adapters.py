"""Statistics Sweden population by age and sex on 31 December 2025.

SCB introduced controlled disclosure perturbation in 2025; totals may not add up.
"""
import release_runtime
import json
import re
import subprocess
BASE = 'https://api.scb.se/OV0104/v1/doris/en/ssd/BE/BE0101/BE0101A/BefolkningR1860NCKM'

def _get(payload=None):
    args = ['/usr/bin/curl', '--fail', '--silent', '--show-error', '--max-time', '25']
    if payload is not None:
        args += ['-H', 'Content-Type: application/json', '--data', json.dumps(payload, ensure_ascii=False)]
    r = release_runtime.run(args + [BASE], capture_output=True, text=True, check=True)
    return json.loads(r.stdout)

def metadata():
    j = _get()
    if not isinstance(j.get('variables'), list):
        raise ValueError('unexpected SCB metadata')
    return j

def population_2025(ages, sexes):
    """Explicit age and sex codes, as returned by metadata; up to 100 cells."""
    for values in (ages, sexes):
        if not isinstance(values, list) or not values or any((not isinstance(v, str) or not re.fullmatch('[A-Za-z0-9+_-]{1,20}', v) for v in values)) or (len(set(values)) != len(values)):
            raise ValueError('invalid selection')
    if len(ages) * len(sexes) > 100:
        raise ValueError('query exceeds 100 cells')
    sels = {'Alder': ages, 'Kon': sexes, 'ContentsCode': ['0000088D'], 'Tid': ['2025']}
    payload = {'query': [{'code': k, 'selection': {'filter': 'item', 'values': v}} for k, v in sels.items()], 'response': {'format': 'json-stat2'}}
    j = _get(payload)
    if j.get('class') != 'dataset' or set(j.get('id', [])) != set(sels):
        raise ValueError('unexpected SCB dataset')
    for k, v in sels.items():
        if set(j['dimension'][k]['category']['index']) != set(v):
            raise ValueError('response selections differ')
    return j
