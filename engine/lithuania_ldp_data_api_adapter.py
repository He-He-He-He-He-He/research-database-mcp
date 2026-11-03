"""Lithuanian State Data Agency public Data Portal API: browse, schema, query."""
import release_runtime
import argparse, json, re, subprocess
BASE = 'https://api.dataportal.gov.lt'
MAX_BYTES = 4000000

def _part(value):
    if not isinstance(value, str) or not re.fullmatch('[A-Za-z0-9_.-]{1,150}', value) or '..' in value or (value in ('.', '..')):
        raise ValueError('invalid namespace or table identifier')
    return value

def _get(path, body=None):
    cmd = ['/usr/bin/curl', '-q', '--fail', '--silent', '--show-error', '--compressed', '--max-time', '30', '--max-filesize', str(MAX_BYTES)]
    if body is not None:
        cmd += ['-H', 'Content-Type: application/json', '--data-binary', '@-']
    cmd.append(BASE + path)
    r = release_runtime.run(cmd, input=None if body is None else json.dumps(body, ensure_ascii=False).encode(), capture_output=True, timeout=35)
    if r.returncode:
        raise RuntimeError('Lithuanian Data Portal request failed (curl ' + str(r.returncode) + ')')
    if len(r.stdout) > MAX_BYTES:
        raise ValueError('response exceeds 4 MB')
    obj = json.loads(r.stdout)
    if not isinstance(obj, dict) or obj.get('success') is False or 'error' in obj:
        raise ValueError('unexpected API response')
    return {'source': BASE + path, 'response': obj}

def namespaces(namespace=None):
    return _get('/namespaces' + ('/' + _part(namespace) if namespace else ''))

def schema(namespace, table):
    return _get('/namespaces/' + _part(namespace) + '/tables/' + _part(table) + '/schema')

def query(namespace, table, limit=10, offset=0, select=None, filter=None, sort=None):
    if any((isinstance(x, bool) or not isinstance(x, int) for x in (limit, offset))) or not 1 <= limit <= 100 or (not 0 <= offset <= 100000):
        raise ValueError('limit 1–100 and offset 0–100000 required')
    body = {'limit': limit, 'offset': offset}
    for k, v in [('select', select), ('filter', filter), ('sort', sort)]:
        if v is not None:
            if not isinstance(v, str) or not v or len(v) > 500 or any((ord(c) < 32 for c in v)):
                raise ValueError('invalid ' + k)
            body[k] = v
    r = _get('/namespaces/' + _part(namespace) + '/tables/' + _part(table) + '/query', body)
    if not isinstance(r['response'].get('data'), list):
        raise ValueError('unexpected query data')
    r['query'] = body
    r['note'] = 'Portal hosts many publishers; consult original dataset metadata for provenance, definition, unit, licence and time. Pagination is offset based.'
    return r

def main():
    p = argparse.ArgumentParser(description=__doc__)
    s = p.add_subparsers(dest='command', required=True)
    x = s.add_parser('namespaces')
    x.add_argument('namespace', nargs='?')
    x = s.add_parser('schema')
    x.add_argument('namespace')
    x.add_argument('table')
    x = s.add_parser('query')
    x.add_argument('namespace')
    x.add_argument('table')
    x.add_argument('--limit', type=int, default=10)
    x.add_argument('--offset', type=int, default=0)
    x.add_argument('--select')
    x.add_argument('--filter')
    x.add_argument('--sort')
    a = p.parse_args()
    try:
        out = namespaces(a.namespace) if a.command == 'namespaces' else schema(a.namespace, a.table) if a.command == 'schema' else query(a.namespace, a.table, a.limit, a.offset, a.select, a.filter, a.sort)
        print(json.dumps(out, ensure_ascii=False, indent=2))
    except (ValueError, RuntimeError) as e:
        p.exit(1, str(e) + '\n')
if __name__ == '__main__':
    main()
