"""Read-only UniProtKB protein search and record retrieval."""
import release_runtime
import argparse
import json
import re
import subprocess
from urllib.parse import urlencode
BASE = 'https://rest.uniprot.org/uniprotkb'

def _get(url):
    result = release_runtime.run(['/usr/bin/curl', '--fail', '--silent', '--show-error', '--compressed', '--max-time', '25', url], capture_output=True, text=True, check=True)
    value = json.loads(result.stdout)
    if not isinstance(value, dict):
        raise ValueError('unexpected UniProt response')
    return value

def search_proteins(query, size=10):
    if not isinstance(query, str) or not query.strip():
        raise ValueError('query must be non-empty')
    if isinstance(size, bool) or not isinstance(size, int) or (not 1 <= size <= 100):
        raise ValueError('size must be an integer between 1 and 100')
    data = _get(BASE + '/search?' + urlencode({'query': query.strip(), 'format': 'json', 'size': size}))
    if not isinstance(data.get('results'), list):
        raise ValueError('missing results list')
    return data

def get_protein(accession):
    if not isinstance(accession, str) or not re.fullmatch('[A-Z0-9]{6,10}', accession):
        raise ValueError('accession must contain 6–10 uppercase letters or digits')
    data = _get(BASE + '/' + accession + '.json')
    if not data.get('primaryAccession'):
        raise ValueError('missing primary accession')
    return data

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    search = commands.add_parser('search')
    search.add_argument('query')
    search.add_argument('--size', type=int, default=10)
    detail = commands.add_parser('detail')
    detail.add_argument('accession')
    args = parser.parse_args()
    result = search_proteins(args.query, args.size) if args.command == 'search' else get_protein(args.accession)
    print(json.dumps(result, ensure_ascii=False, indent=2))
if __name__ == '__main__':
    main()
