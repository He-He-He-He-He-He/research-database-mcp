"""Local-only Springer Nature Meta API bibliographic lookup; never return abstracts."""
import release_runtime
import argparse
import json
import re
import subprocess
from urllib.parse import urlencode
ENDPOINT = 'https://api.springernature.com/meta/v2/json'
SERVICE = 'research-toolkit-springer-meta'
ACCOUNT = 'zju-research-toolkit'

def _key():
    proc = release_runtime.run(['/usr/bin/security', 'find-generic-password', '-s', SERVICE, '-a', ACCOUNT, '-w'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=20)
    if proc.returncode:
        raise RuntimeError('Cannot read Springer key from macOS Keychain; check the login keychain and access permission.')
    key = proc.stdout.decode('utf-8').strip()
    if not re.fullmatch('[A-Za-z0-9]{16,128}', key):
        raise ValueError('Invalid Springer key format in Keychain.')
    return key

def search(query, limit=5, start=1):
    """Return a small allowlist of bibliographic fields, never full records or abstracts."""
    if not isinstance(query, str) or not query.strip() or len(query) > 300 or any((ord(c) < 32 for c in query)):
        raise ValueError('query must contain 1–300 printable characters')
    if isinstance(limit, bool) or not isinstance(limit, int) or (not 1 <= limit <= 10):
        raise ValueError('limit must be between 1 and 10')
    if isinstance(start, bool) or not isinstance(start, int) or (not 1 <= start <= 1000):
        raise ValueError('start must be between 1 and 1000')
    url = ENDPOINT + '?' + urlencode({'q': query, 'p': limit, 's': start, 'api_key': _key()})
    try:
        proc = release_runtime.run(['/usr/bin/curl', '-q', '--fail', '--silent', '--show-error', '--compressed', '--max-time', '25', '--max-filesize', '2000000', '--config', '-'], input=('url = "' + url + '"\n').encode(), stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=30)
    except (OSError, subprocess.TimeoutExpired):
        raise RuntimeError('Springer Meta API network request failed') from None
    finally:
        url = None
    if proc.returncode:
        raise RuntimeError('Springer Meta API request failed (curl exit ' + str(proc.returncode) + ')')
    raw = proc.stdout
    if len(raw) > 2000000:
        raise ValueError('Springer response exceeds size limit')
    obj = json.loads(raw)
    if not isinstance(obj, dict) or not isinstance(obj.get('records'), list):
        raise ValueError('Unexpected Springer Meta API response')
    fields = ('title', 'doi', 'publicationName', 'publicationDate', 'contentType', 'publisher', 'openaccess', 'identifier', 'language')
    records = []
    for item in obj['records']:
        if not isinstance(item, dict):
            raise ValueError('Unexpected Springer record')
        clean = {k: item[k] for k in fields if k in item and isinstance(item[k], (str, bool, int, float))}
        if isinstance(item.get('creators'), list):
            clean['creators'] = [x['creator'] for x in item['creators'] if isinstance(x, dict) and isinstance(x.get('creator'), str)]
        records.append(clean)
    return {'source': ENDPOINT, 'query': query, 'result': obj.get('result', []), 'records': records, 'note': 'Bibliographic fields only. No abstracts or full text. Check applicable source licences and Springer API terms.'}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('query')
    p.add_argument('--limit', type=int, default=5)
    p.add_argument('--start', type=int, default=1)
    a = p.parse_args()
    try:
        print(json.dumps(search(a.query, a.limit, a.start), ensure_ascii=False, indent=2))
    except (ValueError, RuntimeError) as exc:
        p.exit(1, str(exc) + '\n')
if __name__ == '__main__':
    main()
