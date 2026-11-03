"""Banco de España statistical series API, preserving original metadata."""
import release_runtime
import json
import re
import subprocess
from urllib.parse import urlencode
BASE = 'https://app.bde.es/bierest/resources/srdatosapp/'

def _get(endpoint, codes, language, span=None):
    if language not in ('en', 'es'):
        raise ValueError('language must be en or es')
    if not isinstance(codes, list) or not 1 <= len(codes) <= 20 or any((not isinstance(c, str) or not re.fullmatch('[A-Za-z0-9_.#%\\-]+', c) for c in codes)):
        raise ValueError('Provide 1–20 valid series codes')
    params = {'idioma': language, 'series': ','.join(codes)}
    if span is not None:
        if not re.fullmatch('(?:\\d{4}|3M|12M|30M|36M|60M|MAX)', str(span)):
            raise ValueError('Invalid range')
        params['rango'] = str(span)
    result = release_runtime.run(['/usr/bin/curl', '-q', '--compressed', '-fsSL', '--max-time', '30', '--max-filesize', '8388608', BASE + endpoint + '?' + urlencode(params)], capture_output=True, timeout=35)
    if result.returncode:
        raise RuntimeError('Banco de España request failed: ' + result.stderr.decode('utf-8', 'replace').strip())
    if len(result.stdout) > 8388608:
        raise RuntimeError('Response exceeds 8 MiB')
    return json.loads(result.stdout)

def latest(codes, language='en'):
    return _get('favoritas', codes, language)

def series(codes, span='MAX', language='en'):
    return _get('listaSeries', codes, language, span)
