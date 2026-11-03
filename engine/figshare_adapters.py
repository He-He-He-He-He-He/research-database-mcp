"""Read-only Figshare public record search and detail."""
import release_runtime
import argparse
import json
import subprocess
BASE = 'https://api.figshare.com/v2/articles'

def _request(url, payload=None):
    cmd = ['/usr/bin/curl', '--fail', '--silent', '--show-error', '--compressed', '--max-time', '25']
    if payload is not None:
        cmd += ['--header', 'Content-Type: application/json', '--data-binary', '@-']
    cmd.append(url)
    result = release_runtime.run(cmd, input=None if payload is None else json.dumps(payload), capture_output=True, text=True, check=True)
    return json.loads(result.stdout)

def search_records(query, page_size=10, page=1):
    if not isinstance(query, str) or len(query.strip()) < 4:
        raise ValueError('query must contain at least four characters')
    if isinstance(page_size, bool) or not isinstance(page_size, int) or (not 1 <= page_size <= 100):
        raise ValueError('page_size must be 1 to 100')
    if isinstance(page, bool) or not isinstance(page, int) or (not 1 <= page <= 100):
        raise ValueError('page must be 1 to 100')
    data = _request(BASE + '/search', {'search_for': query.strip(), 'page_size': page_size, 'page': page})
    if not isinstance(data, list):
        raise ValueError('unexpected Figshare search response')
    return data

def get_record(record_id):
    if isinstance(record_id, bool) or not isinstance(record_id, int) or record_id <= 0:
        raise ValueError('record_id must be a positive integer')
    data = _request(BASE + '/' + str(record_id))
    if not isinstance(data, dict) or data.get('id') != record_id:
        raise ValueError('unexpected Figshare record')
    return data

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    search = commands.add_parser('search')
    search.add_argument('query')
    search.add_argument('--page-size', type=int, default=10)
    search.add_argument('--page', type=int, default=1)
    detail = commands.add_parser('detail')
    detail.add_argument('record_id', type=int)
    args = parser.parse_args()
    result = search_records(args.query, args.page_size, args.page) if args.command == 'search' else get_record(args.record_id)
    print(json.dumps(result, ensure_ascii=False, indent=2))
if __name__ == '__main__':
    main()
