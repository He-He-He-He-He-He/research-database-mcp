"""Kenya National Bureau of Statistics repository: publication search and assets."""
import release_runtime
import argparse, json, re
import requests
BASE = 'https://repository.knbs.or.ke/server/api/'

def _uuid(value):
    if not isinstance(value, str) or not re.fullmatch('[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}', value):
        raise ValueError('无效 UUID')
    return value

def _get(path, params=None):
    s = requests.Session()
    s.trust_env = False
    r = s.get(BASE + path, params=params, timeout=30, stream=True)
    r.raise_for_status()
    pieces = []
    size = 0
    for c in r.iter_content(65536):
        size += len(c)
        if size > 8000000:
            raise ValueError('响应超过 8 MB')
        pieces.append(c)
    return (r.url, json.loads(b''.join(pieces)))

def search(query, limit=10, page=0):
    if not isinstance(query, str) or not query.strip() or len(query) > 150 or (not 1 <= limit <= 30) or (not 0 <= page <= 1000):
        raise ValueError('搜索或分页参数无效')
    url, j = _get('discover/search/objects', {'query': query, 'size': limit, 'page': page})
    try:
        result = j['_embedded']['searchResult']
        objects = result['_embedded']['objects']
        pagination = result['page']
    except (KeyError, TypeError):
        raise ValueError('目录结构异常')
    rows = []
    for item in objects:
        v = item.get('_embedded', {}).get('indexableObject', {})
        rows.append({'id': v.get('uuid'), 'name': v.get('name'), 'handle': v.get('handle'), 'metadata': v.get('metadata', {}), 'type': v.get('type')})
    return {'source': url, 'page': pagination, 'items': rows, 'note': '检索的是出版物和资料记录，不是逐项统计观测；需核验作者、年份和许可。'}

def item(identifier):
    uid = _uuid(identifier)
    url, j = _get('core/items/' + uid)
    if j.get('uuid') != uid:
        raise ValueError('记录不匹配')
    return {'source': url, 'record': j}

def assets(identifier):
    uid = _uuid(identifier)
    url, j = _get('core/items/' + uid + '/bundles', {'size': 50})
    bundles = j.get('_embedded', {}).get('bundles', [])
    out = []
    for b in bundles:
        if b.get('name') != 'ORIGINAL':
            continue
        bid = _uuid(b.get('uuid'))
        _, v = _get('core/bundles/' + bid + '/bitstreams', {'size': 50})
        for x in v.get('_embedded', {}).get('bitstreams', []):
            fid = _uuid(x.get('uuid'))
            out.append({'id': fid, 'name': x.get('name'), 'size_bytes': x.get('sizeBytes'), 'content_url': BASE + 'core/bitstreams/' + fid + '/content', 'checksum': x.get('checkSum')})
    return {'source': url, 'item_id': uid, 'assets': out, 'note': '仅列出原始附件，不自动下载；链接可用性与访问权限可能因文件而异。'}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    s = p.add_subparsers(dest='cmd', required=True)
    q = s.add_parser('search')
    q.add_argument('query')
    q.add_argument('--limit', type=int, default=10)
    q.add_argument('--page', type=int, default=0)
    q = s.add_parser('item')
    q.add_argument('identifier')
    q = s.add_parser('assets')
    q.add_argument('identifier')
    a = p.parse_args()
    v = search(a.query, a.limit, a.page) if a.cmd == 'search' else item(a.identifier) if a.cmd == 'item' else assets(a.identifier)
    print(json.dumps(v, ensure_ascii=False, indent=2))
if __name__ == '__main__':
    main()
