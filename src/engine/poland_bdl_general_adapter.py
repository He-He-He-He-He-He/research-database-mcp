"""Statistics Poland Local Data Bank (BDL), public read-only API."""
import release_runtime
import argparse, json, re
import requests
BASE = 'https://bdl.stat.gov.pl/api/v1/'
MAX_BYTES = 10 * 1024 * 1024

def _get(path, params=None):
    with requests.get(BASE + path, params=params, timeout=35, stream=True, headers={'User-Agent': 'ResearchToolkit/1.0'}) as r:
        r.raise_for_status()
        chunks = []
        n = 0
        for b in r.iter_content(65536):
            n += len(b)
            if n > MAX_BYTES:
                raise ValueError('Response exceeds 10 MiB')
            chunks.append(b)
        return {'source': r.url, 'result': json.loads(b''.join(chunks))}

def subjects(parent=None, page=0, limit=20):
    if page < 0 or not 1 <= limit <= 100:
        raise ValueError('page >= 0, limit 1–100')
    p = {'lang': 'en', 'page': page, 'page-size': limit}
    if parent:
        if not re.fullmatch('[A-Za-z]\\d+', parent):
            raise ValueError('invalid subject id')
        p['parent-id'] = parent
    return _get('subjects', p)

def subject(identifier):
    if not re.fullmatch('[A-Za-z]\\d+', identifier):
        raise ValueError('invalid subject id')
    return _get('subjects/' + identifier, {'lang': 'en'})

def variables(subject_id, page=0, limit=20):
    if not re.fullmatch('[A-Za-z]\\d+', subject_id) or page < 0 or (not 1 <= limit <= 100):
        raise ValueError('invalid subject/page/limit')
    return _get('variables', {'subject-id': subject_id, 'lang': 'en', 'page': page, 'page-size': limit})

def variable(identifier):
    if int(identifier) < 1:
        raise ValueError('invalid variable')
    return _get('variables/' + str(int(identifier)), {'lang': 'en'})

def units(level=0, page=0, limit=20):
    if not 0 <= int(level) <= 7 or page < 0 or (not 1 <= limit <= 100):
        raise ValueError('invalid level/page/limit')
    return _get('units', {'level': int(level), 'lang': 'en', 'page': page, 'page-size': limit})

def data(unit, variable_id, year):
    if not re.fullmatch('\\d{12}', unit) or int(variable_id) < 1 or (not 1900 <= int(year) <= 2100):
        raise ValueError('invalid unit, variable or year')
    return _get('data/by-unit/' + unit, {'var-id': int(variable_id), 'year': int(year), 'lang': 'en'})

def main():
    p = argparse.ArgumentParser()
    s = p.add_subparsers(dest='cmd', required=True)
    q = s.add_parser('subjects')
    q.add_argument('--parent')
    q.add_argument('--page', type=int, default=0)
    q.add_argument('--limit', type=int, default=20)
    q = s.add_parser('subject')
    q.add_argument('identifier')
    q = s.add_parser('variables')
    q.add_argument('subject_id')
    q.add_argument('--page', type=int, default=0)
    q.add_argument('--limit', type=int, default=20)
    q = s.add_parser('variable')
    q.add_argument('identifier')
    q = s.add_parser('units')
    q.add_argument('--level', type=int, default=0)
    q.add_argument('--page', type=int, default=0)
    q.add_argument('--limit', type=int, default=20)
    q = s.add_parser('data')
    q.add_argument('unit')
    q.add_argument('variable_id')
    q.add_argument('year')
    a = p.parse_args()
    if a.cmd == 'subjects':
        d = subjects(a.parent, a.page, a.limit)
    elif a.cmd == 'subject':
        d = subject(a.identifier)
    elif a.cmd == 'variables':
        d = variables(a.subject_id, a.page, a.limit)
    elif a.cmd == 'variable':
        d = variable(a.identifier)
    elif a.cmd == 'units':
        d = units(a.level, a.page, a.limit)
    else:
        d = data(a.unit, a.variable_id, a.year)
    print(json.dumps(d, ensure_ascii=False, indent=2))
if __name__ == '__main__':
    main()
