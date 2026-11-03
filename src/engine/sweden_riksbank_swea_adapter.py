"""Riksbank SWEA official interest and exchange rates API."""
import release_runtime
import json
import re
import subprocess
from datetime import date
BASE = 'https://api.riksbank.se/swea/v1/'

def _get(path):
    p = release_runtime.run(['curl', '--compressed', '-fsSL', '--max-time', '25', '--max-filesize', '8388608', BASE + path], capture_output=True, timeout=30)
    if p.returncode:
        raise RuntimeError('Riksbank request failed: ' + p.stderr.decode('utf8', 'replace').strip())
    if len(p.stdout) > 8388608:
        raise RuntimeError('Response exceeds 8 MiB')
    return json.loads(p.stdout)

def _series(code):
    if not isinstance(code, str) or not re.fullmatch('[A-Za-z0-9_]+', code):
        raise ValueError('Invalid series ID')
    return code

def groups():
    return _get('Groups')

def series():
    return _get('Series')

def latest(code):
    return _get('Observations/Latest/' + _series(code))

def observations(code, start, end):
    a, b = (date.fromisoformat(start), date.fromisoformat(end))
    if a > b:
        raise ValueError('Start must not exceed end')
    return _get('Observations/' + _series(code) + '/' + a.isoformat() + '/' + b.isoformat())
