"""Read-only RCSB PDB full-text entry search and entry metadata."""
import release_runtime
import argparse
import json
import re
import subprocess
from urllib.parse import urlencode

def _get(url):
    result = release_runtime.run(['/usr/bin/curl', '--fail', '--silent', '--show-error', '--compressed', '--max-time', '25', '--write-out', '\n%{http_code}', url], capture_output=True, text=True, check=True)
    body, status = result.stdout.rsplit('\n', 1)
    if status == '204':
        return None
    data = json.loads(body)
    if not isinstance(data, dict):
        raise ValueError('unexpected RCSB response')
    return data

def search_entries(query, limit=10, offset=0):
    if not isinstance(query, str) or not query.strip():
        raise ValueError('query must be non-empty')
    if isinstance(limit, bool) or not isinstance(limit, int) or (not 1 <= limit <= 100):
        raise ValueError('limit must be an integer from 1 to 100')
    if isinstance(offset, bool) or not isinstance(offset, int) or (not 0 <= offset <= 100000):
        raise ValueError('offset must be an integer from 0 to 100000')
    payload = {'query': {'type': 'terminal', 'service': 'full_text', 'parameters': {'value': query.strip()}}, 'return_type': 'entry', 'request_options': {'paginate': {'start': offset, 'rows': limit}}}
    data = _get('https://search.rcsb.org/rcsbsearch/v2/query?' + urlencode({'json': json.dumps(payload, separators=(',', ':'))}))
    if data is None:
        return {'total_count': 0, 'result_set': []}
    if not isinstance(data.get('result_set'), list):
        raise ValueError('missing result_set')
    return data

def get_entry(pdb_id):
    if not isinstance(pdb_id, str) or not re.fullmatch('[0-9][A-Za-z0-9]{3}', pdb_id):
        raise ValueError('pdb_id must be a four-character PDB ID, e.g. 4HHB')
    key = pdb_id.upper()
    data = _get('https://data.rcsb.org/rest/v1/core/entry/' + key)
    if data is None or data.get('rcsb_id') != key:
        raise ValueError('unexpected PDB ID')
    return data

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    search = commands.add_parser('search')
    search.add_argument('query')
    search.add_argument('--limit', type=int, default=10)
    search.add_argument('--offset', type=int, default=0)
    detail = commands.add_parser('detail')
    detail.add_argument('pdb_id')
    args = parser.parse_args()
    result = search_entries(args.query, args.limit, args.offset) if args.command == 'search' else get_entry(args.pdb_id)
    print(json.dumps(result, ensure_ascii=False, indent=2))
if __name__ == '__main__':
    main()
