"""Swiss National Bank data portal: topics, cube metadata and time series."""
import release_runtime
import json
import re
import subprocess
from datetime import date
from urllib.parse import urlencode
BASE = 'https://data.snb.ch'

def _get(path, params=None):
    url = BASE + path + ('?' + urlencode(params) if params else '')
    proc = release_runtime.run(['/usr/bin/curl', '-q', '--compressed', '-fsSL', '--max-time', '30', '--max-filesize', '8388608', url], capture_output=True, timeout=35)
    if proc.returncode:
        raise RuntimeError('SNB request failed: ' + proc.stderr.decode('utf8', 'replace').strip())
    if len(proc.stdout) > 8388608:
        raise RuntimeError('Response exceeds 8 MiB')
    return json.loads(proc.stdout)

def _lang(lang):
    if lang not in ('en', 'de', 'fr'):
        raise ValueError('Language must be en, de or fr')
    return lang

def _cube(cube):
    if not isinstance(cube, str) or not re.fullmatch('[A-Za-z0-9_]+', cube):
        raise ValueError('Invalid cube ID')
    return cube

def _viewtime():
    return _get('/json/application/properties')['pageViewTime']

def catalog(lang='en'):
    return _get('/json/topic/getTopicsWithRootSubTopics', {'lang': _lang(lang), 'pageViewTime': _viewtime(), 'expanded': 'true'})

def metadata(cube, lang='en'):
    return _get('/json/table/getCubeInfo', {'cubeId': _cube(cube), 'lang': _lang(lang), 'isWarehouse': 'false', 'pageViewTime': _viewtime()})

def dimensions(cube, lang='en'):
    return _get('/api/cube/' + _cube(cube) + '/dimensions/' + _lang(lang))

def observations(cube, start, end, lang='en'):
    a, b = (date.fromisoformat(start), date.fromisoformat(end))
    if a > b:
        raise ValueError('start must not exceed end')
    return _get('/api/cube/' + _cube(cube) + '/data/json/' + _lang(lang), {'fromDate': a.isoformat(), 'toDate': b.isoformat()})
