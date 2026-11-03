"""Statbel be.STAT standard-view catalog, metadata and JSON observations."""
import release_runtime
import argparse, json, re, subprocess
BASE = 'https://bestat.statbel.fgov.be/bestat/api/'
MAX = 10000000

def _get(path):
    p = release_runtime.run(['/usr/bin/curl', '-q', '--fail', '--silent', '--show-error', '--compressed', '--max-time', '35', '--max-filesize', str(MAX), BASE + path], capture_output=True, timeout=40)
    if p.returncode:
        raise RuntimeError('be.STAT request failed (curl ' + str(p.returncode) + ')')
    if len(p.stdout) > MAX:
        raise ValueError('response exceeds 10 MB; use a smaller view')
    return json.loads(p.stdout)

def _id(v):
    if not isinstance(v, str) or not re.fullmatch('[0-9a-fA-F]{8}-(?:[0-9a-fA-F]{4}-){3}[0-9a-fA-F]{12}', v):
        raise ValueError('view id must be a UUID')
    return v

def views(keyword='', limit=30, offset=0):
    if not isinstance(keyword, str) or len(keyword) > 150 or any((isinstance(x, bool) or not isinstance(x, int) for x in (limit, offset))) or (not 1 <= limit <= 100) or (offset < 0):
        raise ValueError('invalid search or pagination')
    obj = _get('views/')
    if not isinstance(obj, list):
        raise ValueError('unexpected views response')
    matches = [v for v in obj if keyword.casefold() in str(v.get('name', '')).casefold()]
    return {'source': BASE + 'views/', 'total_views': len(obj), 'matched': len(matches), 'offset': offset, 'views': matches[offset:offset + limit], 'note': 'Filtered and paginated locally. Names may use different languages.'}

def view(view_id):
    view_id = _id(view_id)
    obj = _get('views/' + view_id)
    if not isinstance(obj, dict) or obj.get('id', '').lower() != view_id.lower():
        raise ValueError('unexpected view metadata')
    return {'source': BASE + 'views/' + view_id, 'view': obj}

def observations(view_id, limit=30, offset=0):
    view_id = _id(view_id)
    if any((isinstance(x, bool) or not isinstance(x, int) for x in (limit, offset))) or not 1 <= limit <= 100 or offset < 0:
        raise ValueError('invalid pagination')
    path = 'views/' + view_id + '/result/JSON'
    obj = _get(path)
    if not isinstance(obj, dict) or not isinstance(obj.get('facts'), list):
        raise ValueError('unexpected view data')
    facts = obj['facts']
    return {'source': BASE + path, 'total': len(facts), 'offset': offset, 'facts': facts[offset:offset + limit], 'note': 'One predefined view, not the complete underlying datasource. Pagination local after downloading view; verify source, dimension, unit and date. Official totals may not reflect view filters.'}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    s = p.add_subparsers(dest='cmd', required=True)
    x = s.add_parser('views')
    x.add_argument('--keyword', default='')
    x.add_argument('--limit', type=int, default=30)
    x.add_argument('--offset', type=int, default=0)
    x = s.add_parser('view')
    x.add_argument('id')
    x = s.add_parser('data')
    x.add_argument('id')
    x.add_argument('--limit', type=int, default=30)
    x.add_argument('--offset', type=int, default=0)
    a = p.parse_args()
    try:
        print(json.dumps(views(a.keyword, a.limit, a.offset) if a.cmd == 'views' else view(a.id) if a.cmd == 'view' else observations(a.id, a.limit, a.offset), ensure_ascii=False, indent=2))
    except (ValueError, RuntimeError) as e:
        p.exit(1, str(e) + '\n')
if __name__ == '__main__':
    main()
