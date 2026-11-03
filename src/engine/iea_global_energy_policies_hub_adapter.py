"""IEA Global Energy Policies Hub public website API."""
import release_runtime
import json
import subprocess
from urllib.parse import urlencode
BASE = 'https://api.iea.org/v3/policies'
PAGE = 'https://www.iea.org/data-and-statistics/data-tools/global-energy-policies-hub'
MAX_BYTES = 8000000

def _get(path='', params=None):
    url = BASE + path + ('?' + urlencode(params) if params else '')
    r = release_runtime.run(['/usr/bin/curl', '--fail', '--silent', '--show-error', '--compressed', '--max-time', '35', '--max-filesize', str(MAX_BYTES), url], capture_output=True, timeout=40)
    if r.returncode:
        raise RuntimeError('IEA request failed: ' + r.stderr.decode('utf-8', 'replace')[:500])
    if len(r.stdout) > MAX_BYTES:
        raise ValueError('IEA response too large')
    rows = json.loads(r.stdout)
    if not isinstance(rows, list):
        raise ValueError('unexpected response')
    return (url, rows)

def topics():
    url, rows = _get('/list/topic')
    if any((not isinstance(x, str) for x in rows)):
        raise ValueError('unexpected topics')
    return {'source': url, 'page': PAGE, 'topics': rows}

def search(country, topic, limit=20, offset=0):
    if any((not isinstance(x, str) or not x.strip() or len(x) > 120 for x in (country, topic))):
        raise ValueError('invalid filters')
    if any((isinstance(x, bool) or not isinstance(x, int) for x in (limit, offset))) or not 1 <= limit <= 100 or offset < 0:
        raise ValueError('invalid pagination')
    url, rows = _get('', {'country': country, 'topic': topic})
    if any((not isinstance(r, dict) or topic not in r.get('topics', []) or (not any((isinstance(c, dict) and c.get('name') == country for c in r.get('countries', [])))) for r in rows)):
        raise ValueError('unexpected/out-of-filter response')
    return {'source': url, 'page': PAGE, 'page_updated': '2026-06-24', 'total': len(rows), 'offset': offset, 'limit': limit, 'rows': rows[offset:offset + limit], 'note': 'IEA compiled policy directory, not a comprehensive legal source. Status may be stale, descriptions can be HTML, source links may be secondary. Check official legal text and current status. International and country categories overlap. Country and topic from explorer; pagination local.'}
