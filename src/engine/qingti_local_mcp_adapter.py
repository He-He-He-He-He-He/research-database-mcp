"""Read-only adapter for the official, locally running Qingti MCP server."""
import release_runtime
import argparse
import json
import requests
URL = 'http://127.0.0.1:49528/mcp'
HEADERS = {'Accept': 'application/json, text/event-stream', 'Content-Type': 'application/json'}

def _call(name, arguments):
    payload = {'jsonrpc': '2.0', 'id': 1, 'method': 'tools/call', 'params': {'name': name, 'arguments': arguments}}
    response = requests.post(URL, json=payload, headers=HEADERS, timeout=15, proxies={'http': None, 'https': None})
    response.raise_for_status()
    data = response.json()
    if data.get('error'):
        raise RuntimeError('Qingti MCP returned a protocol error')
    result = data.get('result') or {}
    if result.get('isError'):
        raise RuntimeError('Qingti MCP tool reported an error')
    parts = [x.get('text') for x in result.get('content', []) if x.get('type') == 'text']
    if len(parts) != 1:
        raise ValueError('Unexpected Qingti MCP response')
    return json.loads(parts[0])

def status():
    data = _call('qt_get_status', {})
    return {'source': 'Qingti official local MCP', 'logged_in': data.get('logged_in')}

def search(query, limit=10, page=1):
    if not isinstance(query, str) or not query.strip() or len(query) > 200:
        raise ValueError('query must be 1–200 characters')
    if not isinstance(limit, int) or not 1 <= limit <= 20:
        raise ValueError('limit must be 1–20')
    if not isinstance(page, int) or not 1 <= page <= 1000:
        raise ValueError('page must be 1–1000')
    data = _call('qt_search_articles', {'query': query.strip(), 'field': 'title', 'limit': limit, 'page': page, 'show_in_window': False})
    if not isinstance(data.get('results'), list):
        raise ValueError('unexpected Qingti search response')
    return {'source': 'Qingti local personal library', 'query': query.strip(), 'results': data['results'], 'total': data.get('total'), 'page': data.get('page'), 'has_more': data.get('has_more')}
if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('query', nargs='?')
    p.add_argument('--limit', type=int, default=10)
    p.add_argument('--page', type=int, default=1)
    a = p.parse_args()
    print(json.dumps(search(a.query, a.limit, a.page) if a.query else status(), ensure_ascii=False, indent=2))
