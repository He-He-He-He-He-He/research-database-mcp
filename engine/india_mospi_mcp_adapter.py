"""India MoSPI official e-Sankhyiki MCP read-only discovery and data calls."""
import release_runtime
import argparse, json, re
import requests
URL = 'https://mcp.mospi.gov.in/'
HEADERS = {'Accept': 'application/json, text/event-stream', 'Content-Type': 'application/json', 'MCP-Protocol-Version': '2025-03-26', 'User-Agent': 'ResearchToolkit/1.0'}
ALLOWED = {'list_datasets', 'get_indicators', 'get_metadata', 'get_data'}

def _rpc(method, params):
    payload = {'jsonrpc': '2.0', 'id': 1, 'method': method, 'params': params}
    with requests.post(URL, json=payload, headers=HEADERS, timeout=45, stream=True) as r:
        r.raise_for_status()
        chunks = []
        size = 0
        for c in r.iter_content(65536):
            size += len(c)
            if size > 8 * 1024 * 1024:
                raise ValueError('response exceeds 8 MiB')
            chunks.append(c)
        raw = b''.join(chunks).decode('utf-8')
        kind = r.headers.get('content-type', '')
    if 'text/event-stream' in kind:
        events = [x[5:].strip() for x in raw.splitlines() if x.startswith('data:')]
        if len(events) != 1:
            raise ValueError('unexpected event-stream response')
        d = json.loads(events[0])
    else:
        d = json.loads(raw)
    if 'error' in d:
        raise RuntimeError('MCP error: ' + str(d['error'])[:400])
    return d['result']

def schema():
    return {'source': URL, 'result': _rpc('tools/list', {})}

def call(tool, arguments):
    if tool not in ALLOWED or not isinstance(arguments, dict):
        raise ValueError('unsupported tool or arguments')
    if 'user_query' in arguments:
        raise ValueError('user_query telemetry is disabled by this adapter')
    if tool != 'list_datasets' and (not re.fullmatch('[A-Z0-9_]{2,30}', str(arguments.get('dataset', '')))):
        raise ValueError('invalid dataset')
    args = dict(arguments)
    if tool == 'get_data':
        f = args.get('filters')
        if not isinstance(f, dict) or len(f) > 30:
            raise ValueError('invalid filters')
        f = dict(f)
        limit = int(f.get('limit', 20))
        if not 1 <= limit <= 100:
            raise ValueError('limit must be 1–100')
        f['limit'] = str(limit)
        args['filters'] = f
    if len(json.dumps(args, ensure_ascii=False)) > 5000:
        raise ValueError('arguments exceed limit')
    d = _rpc('tools/call', {'name': tool, 'arguments': args})
    v = d.get('structuredContent')
    if d.get('isError') or (isinstance(v, dict) and ('error' in v or v.get('statusCode') is False)):
        raise RuntimeError('MoSPI upstream error: ' + str(v)[:500])
    return {'source': URL, 'tool': tool, 'arguments': args, 'result': v if v is not None else d.get('content')}

def main():
    p = argparse.ArgumentParser()
    p.add_argument('tool', choices=['schema', *sorted(ALLOWED)])
    p.add_argument('arguments', nargs='?', default='{}', help='JSON object')
    a = p.parse_args()
    d = schema() if a.tool == 'schema' else call(a.tool, json.loads(a.arguments))
    print(json.dumps(d, ensure_ascii=False, indent=2))
if __name__ == '__main__':
    main()
