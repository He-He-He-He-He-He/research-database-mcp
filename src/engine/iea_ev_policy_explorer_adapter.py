"""IEA Global EV Policy Explorer website's public policy records."""
import release_runtime
import json
import subprocess
URL = 'https://iea.blob.core.windows.net/scripts/ev-policies/data/policies.json'
PAGE = 'https://www.iea.org/data-and-statistics/data-tools/global-ev-policy-explorer'
MAX_BYTES = 5000000

def _load():
    r = release_runtime.run(['/usr/bin/curl', '--fail', '--silent', '--show-error', '--compressed', '--max-time', '35', '--max-filesize', str(MAX_BYTES), URL], capture_output=True, timeout=40)
    if r.returncode:
        raise RuntimeError('IEA policy download failed: ' + r.stderr.decode('utf-8', 'replace')[:500])
    if len(r.stdout) > MAX_BYTES:
        raise ValueError('IEA response too large')
    rows = json.loads(r.stdout)
    if not isinstance(rows, list) or any((not isinstance(x, dict) for x in rows)):
        raise ValueError('unexpected IEA response')
    return rows

def search(country='', keyword='', policy_type='', limit=20, offset=0):
    for s in (country, keyword, policy_type):
        if not isinstance(s, str) or len(s) > 150:
            raise ValueError('invalid filter')
    if any((isinstance(x, bool) or not isinstance(x, int) for x in (limit, offset))) or not 1 <= limit <= 100 or offset < 0:
        raise ValueError('invalid pagination')
    rows = _load()
    chosen = [r for r in rows if (not country or country.casefold() == str(r.get('country', '')).casefold()) and (not policy_type or policy_type.casefold() == str(r.get('policyType', '')).casefold()) and (not keyword or keyword.casefold() in json.dumps(r, ensure_ascii=False).casefold())]
    return {'source': URL, 'explorer': PAGE, 'explorer_updated': '2026-05-20', 'total': len(chosen), 'offset': offset, 'limit': limit, 'rows': chosen[offset:offset + limit], 'note': 'IEA compiled policy descriptions are not exhaustive or a legal determination. Announced year can differ from effective date; proposals and targets are not enacted law. Original source and current legal status require verification; some sources are secondary. Filters run locally; preserve missing years and linked sources.'}
