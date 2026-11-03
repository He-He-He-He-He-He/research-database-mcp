"""Estonian parliament official open-data API for draft legislation."""
import release_runtime
import re
import requests
BASE = 'https://api.riigikogu.ee/api/volumes/drafts'
DOC = 'https://api.riigikogu.ee/swagger-ui/index.html'
SCOPE = '爱沙尼亚议会官方草案与程序数据；保留原始语种和状态，草案不等同已生效法律，是否通过及生效应查询官方公报。'

def _get(url, params):
    r = requests.get(url, params=params, timeout=30)
    r.raise_for_status()
    try:
        return r.json()
    except ValueError as exc:
        raise RuntimeError('爱沙尼亚议会 API 返回非 JSON 数据') from exc

def search(title, page=0, size=5, language='ET'):
    if not isinstance(title, str) or not title.strip() or len(title) > 200:
        raise ValueError('标题关键词须为不超过 200 字的非空字符串')
    if isinstance(page, bool) or not isinstance(page, int) or (not 0 <= page <= 1000):
        raise ValueError('page 须为 0 至 1000 的整数，从 0 开始')
    if isinstance(size, bool) or not isinstance(size, int) or (not 1 <= size <= 20):
        raise ValueError('size 须为 1 至 20 的整数')
    if language not in ('ET', 'EN', 'RU'):
        raise ValueError('language 须为 ET、EN 或 RU')
    data = _get(BASE, {'title': title.strip(), 'page': page, 'size': size, 'lang': language})
    try:
        pagination = data['page']
        items = data.get('_embedded', {}).get('content', [])
        if not isinstance(items, list) or not isinstance(pagination['totalElements'], int):
            raise ValueError()
        if pagination['totalElements'] and page < pagination.get('totalPages', 0) and (not items):
            raise ValueError()
    except (KeyError, TypeError, ValueError) as exc:
        raise RuntimeError('议会草案检索返回结构异常') from exc
    return {'source': '爱沙尼亚议会办公室开放数据 API', 'source_url': BASE, 'documentation': DOC, 'title': title, 'language': language, 'pagination': pagination, 'items': items, 'scope': SCOPE}

def detail(identifier, language='ET'):
    if not isinstance(identifier, str) or not re.fullmatch('[0-9a-fA-F]{8}(-[0-9a-fA-F]{4}){3}-[0-9a-fA-F]{12}', identifier):
        raise ValueError('identifier 须为草案 UUID')
    if language not in ('ET', 'EN', 'RU'):
        raise ValueError('language 须为 ET、EN 或 RU')
    url = BASE + '/' + identifier
    data = _get(url, {'lang': language})
    if not isinstance(data, dict) or str(data.get('uuid', '')).lower() != identifier.lower():
        raise RuntimeError('议会草案详情与请求编号不匹配')
    return {'source': '爱沙尼亚议会办公室开放数据 API', 'source_url': url, 'language': language, 'item': data, 'scope': SCOPE}
if __name__ == '__main__':
    import argparse, json
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest='mode', required=True)
    a = sub.add_parser('search')
    a.add_argument('title')
    a.add_argument('--page', type=int, default=0)
    a.add_argument('--size', type=int, default=5)
    a.add_argument('--language', choices=['ET', 'EN', 'RU'], default='ET')
    b = sub.add_parser('detail')
    b.add_argument('identifier')
    b.add_argument('--language', choices=['ET', 'EN', 'RU'], default='ET')
    x = p.parse_args()
    result = search(x.title, x.page, x.size, x.language) if x.mode == 'search' else detail(x.identifier, x.language)
    print(json.dumps(result, ensure_ascii=False, indent=2))
