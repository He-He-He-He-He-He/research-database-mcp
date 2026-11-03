"""World Library DRAA 精选集书目检索；不下载书籍。"""
import release_runtime
import argparse, json, subprocess, sys
ENDPOINT = 'https://worldlibrary.ai/wl-api/search/search'

def search_draa(query, size=10):
    if not isinstance(query, str) or not query.strip() or len(query) > 100 or ('\n' in query) or ('\r' in query):
        raise ValueError('关键词需为 1–100 字单行文本')
    if not isinstance(size, int) or not 1 <= size <= 20:
        raise ValueError('每次返回数量需为 1–20')
    payload = {'search_type': 'keyword', 'query': query.strip(), 'size': size, 'facet_size': 5, 'source_fields': ['title', 'author', 'language', 'publisher', 'publication_year', 'collection', 'document_type', 'page'], 'facet': [], 'collection': ['draa']}
    cmd = ['/usr/bin/curl', '--silent', '--show-error', '--fail', '--max-time', '20', '--header', 'Content-Type: application/json', '--data-binary', json.dumps(payload, ensure_ascii=False), ENDPOINT]
    try:
        r = release_runtime.run(cmd, check=True, capture_output=True, text=True)
    except subprocess.CalledProcessError as e:
        raise RuntimeError('检索请求失败，请检查网络或网站状态') from e
    try:
        data = json.loads(r.stdout)
    except json.JSONDecodeError as e:
        raise RuntimeError('上游未返回 JSON') from e
    if not isinstance(data.get('hits'), list) or not isinstance(data.get('total'), int):
        raise RuntimeError('上游返回结构异常')
    items = [{'id': h.get('id'), **h.get('source', {}), 'read_permission': h.get('permission', {}).get('read')} for h in data['hits']]
    return {'query': query.strip(), 'source': 'World Library DRAA 精选集', 'total': data['total'], 'items': items, 'note': '单页书目；检索及页面可达不证明机构识别或全文权限。'}
if __name__ == '__main__':
    p = argparse.ArgumentParser(description='World Library DRAA 书目检索')
    p.add_argument('query')
    p.add_argument('--size', type=int, default=10)
    a = p.parse_args()
    try:
        print(json.dumps(search_draa(a.query, a.size), ensure_ascii=False, indent=2))
    except (ValueError, RuntimeError) as e:
        print(json.dumps({'error': str(e)}, ensure_ascii=False), file=sys.stderr)
        sys.exit(1)
