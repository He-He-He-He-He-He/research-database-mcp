"""Read-only ChEMBL molecule name search and record detail."""
import release_runtime
import argparse
import json
import re
import subprocess
from urllib.parse import urlencode
BASE = 'https://www.ebi.ac.uk/chembl/api/data/molecule'

def _get(url):
    result = release_runtime.run(['/usr/bin/curl', '--fail', '--silent', '--show-error', '--compressed', '--max-time', '25', url], capture_output=True, text=True, check=True)
    value = json.loads(result.stdout)
    if not isinstance(value, dict):
        raise ValueError('unexpected ChEMBL response')
    return value

def search_molecules(query, limit=10, offset=0):
    if not isinstance(query, str) or not query.strip():
        raise ValueError('query must be a non-empty string')
    if isinstance(limit, bool) or not isinstance(limit, int) or (not 1 <= limit <= 100):
        raise ValueError('limit must be an integer between 1 and 100')
    if isinstance(offset, bool) or not isinstance(offset, int) or (not 0 <= offset <= 100000):
        raise ValueError('offset must be an integer between 0 and 100000')
    data = _get(BASE + '/search.json?' + urlencode({'q': query.strip(), 'limit': limit, 'offset': offset}))
    if not isinstance(data.get('molecules'), list):
        raise ValueError('missing molecules list')
    return data

def get_molecule(chembl_id):
    if not isinstance(chembl_id, str) or not re.fullmatch('CHEMBL[0-9]+', chembl_id):
        raise ValueError('chembl_id must look like CHEMBL25')
    data = _get(BASE + '/' + chembl_id + '.json')
    if data.get('molecule_chembl_id') != chembl_id:
        raise ValueError('unexpected molecule ID')
    return data

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    search = commands.add_parser('search')
    search.add_argument('query')
    search.add_argument('--limit', type=int, default=10)
    search.add_argument('--offset', type=int, default=0)
    detail = commands.add_parser('detail')
    detail.add_argument('chembl_id')
    args = parser.parse_args()
    result = search_molecules(args.query, args.limit, args.offset) if args.command == 'search' else get_molecule(args.chembl_id)
    print(json.dumps(result, ensure_ascii=False, indent=2))
if __name__ == '__main__':
    main()
