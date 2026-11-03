"""Banco de Portugal BPstat API; returns original JSON-stat and metadata."""
import release_runtime
import json
import re
import subprocess
from urllib.parse import urlencode
BASE = 'https://bpstat.bportugal.pt/data/v1/'

def _request(path, params=None):
    url = BASE + path + ('?' + urlencode(params) if params else '')
    result = release_runtime.run(['/usr/bin/curl', '-q', '-fsSL', '--max-time', '30', '--max-filesize', '8388608', url], capture_output=True, timeout=35)
    if result.returncode:
        raise RuntimeError('BPstat request failed: ' + result.stderr.decode('utf-8', 'replace').strip())
    if len(result.stdout) > 8388608:
        raise RuntimeError('BPstat response exceeds 8 MiB')
    return json.loads(result.stdout)

def domains(language='EN'):
    return _request('domains/', {'lang': language})

def datasets(domain, language='EN'):
    return _request('domains/' + _id(domain) + '/datasets/', {'lang': language})

def dimensions(domain, language='EN'):
    return _request('domains/' + _id(domain) + '/dimensions/', {'lang': language})

def series(ids, language='EN'):
    return _request('series/', {'lang': language, 'series_ids': _ids(ids)})

def data(domain, dataset, ids, language='EN'):
    return _request('domains/' + _id(domain) + '/datasets/' + _id(dataset), {'lang': language, 'series_ids': _ids(ids)})

def _id(value):
    value = str(value)
    if not re.fullmatch('[A-Za-z0-9_-]+', value):
        raise ValueError('Invalid identifier')
    return value

def _ids(values):
    values = [str(x) for x in values]
    if not values or len(values) > 20 or any((not x.isdigit() for x in values)):
        raise ValueError('Provide 1–20 numeric series identifiers')
    return ','.join(values)
