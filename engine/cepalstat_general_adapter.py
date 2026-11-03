"""UN ECLAC CEPALSTAT official public API, indicator catalog, metadata, data.

Official documentation: https://statistics.cepal.org/portal/cepalstat/open-data.html?lang=en
All dimensions, units, notes and source metadata remain in the result.
"""
import release_runtime
import json
import re
import subprocess
from urllib.parse import urlencode
BASE = 'https://api-cepalstat.cepal.org/cepalstat/api/v1'
MAX_BYTES = 12000000

def _get(path, params):
    url = BASE + path + '?' + urlencode(params)
    r = release_runtime.run(['/usr/bin/curl', '--fail', '--silent', '--show-error', '--compressed', '--max-time', '45', '--max-filesize', str(MAX_BYTES), url], capture_output=True, timeout=50)
    if r.returncode:
        raise RuntimeError('CEPALSTAT request failed: ' + r.stderr.decode('utf-8', 'replace')[:500])
    if len(r.stdout) > MAX_BYTES:
        raise ValueError('CEPALSTAT response exceeds 12 MB; try a narrower members filter')
    obj = json.loads(r.stdout)
    if obj.get('header', {}).get('success') is not True:
        raise RuntimeError('CEPALSTAT API error: ' + str(obj.get('header', {})))
    return obj

def _lang(lang):
    if lang not in ('en', 'es'):
        raise ValueError('language must be en or es')
    return lang

def _id(indicator):
    if isinstance(indicator, bool) or not isinstance(indicator, int) or (not 1 <= indicator <= 10000):
        raise ValueError('indicator must be an integer from 1 to 10000')
    return indicator

def search(keyword='', lang='en'):
    if not isinstance(keyword, str) or len(keyword) > 200:
        raise ValueError('invalid keyword')
    obj = _get('/thematic-tree', {'lang': _lang(lang)})
    out = []

    def walk(node, parents):
        if not isinstance(node, dict):
            return
        name = node.get('name', '')
        if 'indicator_id' in node and keyword.casefold() in str(name).casefold():
            out.append({'id': node['indicator_id'], 'name': name, 'themes': parents})
        for child in node.get('children', []):
            walk(child, parents + [name])
    walk(obj['body'], [])
    return {'source': BASE + '/thematic-tree', 'matched': len(out), 'indicators': out, 'header': obj['header']}

def metadata(indicator, lang='en'):
    return _get('/indicator/' + str(_id(indicator)) + '/metadata', {'lang': _lang(lang)})

def data(indicator, iso3=None, members=None, lang='en'):
    params = {'lang': _lang(lang)}
    if iso3 is not None and (not isinstance(iso3, str) or not re.fullmatch('[A-Z]{3}', iso3)):
        raise ValueError('iso3 must be three uppercase letters')
    if members is not None:
        if not isinstance(members, str) or not re.fullmatch('\\d+(?:,\\d+){0,49}', members):
            raise ValueError('members must be comma-separated numeric member IDs')
        params['members'] = members
    obj = _get('/indicator/' + str(_id(indicator)) + '/data', params)
    body = obj.get('body')
    if not isinstance(body, dict) or not isinstance(body.get('data'), list):
        raise ValueError('unexpected CEPALSTAT response')
    if iso3 is not None:
        body['data'] = [r for r in body['data'] if r.get('iso3') == iso3]
    return {'source': BASE + '/indicator/' + str(indicator) + '/data', 'iso3_filter': iso3, 'note': 'Dimension IDs require the returned members tables; estimates and projections follow the metadata and source notes.', 'response': obj}
