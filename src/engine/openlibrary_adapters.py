"""Read-only Open Library book search and work metadata."""
import release_runtime
import argparse
import json
import os
import re
import subprocess
from urllib.parse import urlencode, urlsplit, parse_qs
BASE = 'https://openlibrary.org'

def _get(path):
    agent = release_runtime.environment.get('OPENLIBRARY_USER_AGENT', 'LocalResearchToolkit/1.0')
    if '\n' in agent or '\r' in agent:
        raise ValueError('invalid user agent')
    result = release_runtime.run(['/usr/bin/curl', '--fail', '--silent', '--show-error', '--compressed', '--max-time', '25', '--user-agent', agent, BASE + path], capture_output=True, text=True, check=True)
    value = json.loads(result.stdout)
    if not isinstance(value, dict):
        raise ValueError('unexpected response')
    return value

def search_books(query, limit=10, offset=0):
    if not isinstance(query, str) or not query.strip():
        raise ValueError('query must not be empty')
    if isinstance(limit, bool) or not isinstance(limit, int) or (not 1 <= limit <= 100):
        raise ValueError('limit must be an integer from 1 to 100')
    if isinstance(offset, bool) or not isinstance(offset, int) or (not 0 <= offset <= 100000):
        raise ValueError('offset must be an integer from 0 to 100000')
    data = _get('/search.json?' + urlencode({'q': query.strip(), 'limit': limit, 'offset': offset, 'fields': 'key,title,author_name,first_publish_year,edition_count,isbn'}))
    docs = data.get('docs')
    total = data.get('numFound')
    start = data.get('start')
    if not isinstance(docs, list) or type(total) is not int or total < 0 or (type(start) is not int) or (start != offset) or (len(docs) > min(limit, max(0, total - offset))) or any((not isinstance(row, dict) for row in docs)):
        raise ValueError('unexpected search page, count or records')
    return data

def get_work(work_id):
    if not isinstance(work_id, str) or not re.fullmatch('OL[0-9]+W', work_id):
        raise ValueError('work_id must look like OL15414348W')
    path = '/works/' + work_id
    data = _get(path + '.json')
    if data.get('key') != path:
        raise ValueError('unexpected work key')
    return data

def get_editions(work_id, limit=10, offset=0):
    if not isinstance(work_id, str) or not re.fullmatch('OL[0-9]+W', work_id):
        raise ValueError('work_id must look like OL15414348W')
    if isinstance(limit, bool) or not isinstance(limit, int) or (not 1 <= limit <= 100):
        raise ValueError('limit must be an integer from 1 to 100')
    if isinstance(offset, bool) or not isinstance(offset, int) or (not 0 <= offset <= 100000):
        raise ValueError('offset must be an integer from 0 to 100000')
    path = '/works/' + work_id
    data = _get(path + '/editions.json?' + urlencode({'limit': limit, 'offset': offset}))
    links = data.get('links')
    entries = data.get('entries')
    total = data.get('size')
    if not isinstance(links, dict) or links.get('work') != path or (not isinstance(links.get('self'), str)):
        raise ValueError('unexpected edition work or pagination link')
    own = urlsplit(links['self'])
    query = parse_qs(own.query)
    if own.scheme or own.netloc or own.path != path + '/editions.json' or (query.get('limit') != [str(limit)]) or (query.get('offset') != [str(offset)]):
        raise ValueError('unexpected edition pagination link')
    if type(total) is not int or total < 0 or (not isinstance(entries, list)) or (len(entries) > min(limit, max(0, total - offset))) or any((not isinstance(x, dict) for x in entries)):
        raise ValueError('unexpected edition count or entries')
    return data

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    search = sub.add_parser('search')
    search.add_argument('query')
    search.add_argument('--limit', type=int, default=10)
    search.add_argument('--offset', type=int, default=0)
    detail = sub.add_parser('detail')
    detail.add_argument('work_id')
    args = parser.parse_args()
    result = search_books(args.query, args.limit, args.offset) if args.command == 'search' else get_work(args.work_id)
    print(json.dumps(result, ensure_ascii=False, indent=2))
if __name__ == '__main__':
    main()
