"""中国科学院科学数据中心：公开数据资源元数据检索。"""
import release_runtime
import argparse, json, re, subprocess, sys
BASE = 'https://www.casdc.cn'
URL = BASE + '/api/index/getIndexAllResourceByES'

def search(keyword, page=1, size=5):
    if not keyword.strip() or len(keyword) > 150 or (not 1 <= page <= 10000) or (not 1 <= size <= 10):
        raise ValueError('关键词不能为空，页码须大于零，单页为1至10条')
    payload = {'aggregations': [{'field': 'resourceType', 'fieldType': '', 'size': 10}], 'esParameter': [{'field': 'name', 'fieldType': 'text', 'fieldName': '名称', 'connector': 'and', 'operator': 'LK', 'type': 'search', 'value': keyword}], 'highlight': [], 'page': page - 1, 'pageSize': size, 'sorts': []}
    proc = release_runtime.run(['/usr/bin/curl', '--fail', '--silent', '--show-error', '--max-time', '25', '--max-filesize', '5242880', '-H', 'Content-Type: application/json', '--data-binary', json.dumps(payload, ensure_ascii=False), URL], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
    if len(proc.stdout) > 5242880:
        raise ValueError('响应超过大小限制')
    x = json.loads(proc.stdout)
    d = x.get('data') if isinstance(x, dict) else None
    if x.get('code') != 200 or not isinstance(d, dict) or (not isinstance(d.get('sourceList'), list)):
        raise ValueError('上游返回错误或结构变化')
    result = []
    for row in d['sourceList']:
        ident = str(row.get('id') or '')
        safe = bool(re.fullmatch('[a-fA-F0-9]{32}', ident))
        result.append({'id': ident, 'title': row.get('name'), 'doi': row.get('doi'), 'source_id': row.get('sourceId'), 'cstr': row.get('cstr'), 'subjects': row.get('subject'), 'keywords': row.get('keywords'), 'license': row.get('license'), 'detail_url': BASE + '/dataDetails/' + ident if safe else None})
    return {'source': 'https://www.casdc.cn/source', 'keyword': keyword, 'page': page, 'page_size': size, 'total': d.get('total'), 'items': result, 'scope': '科学数据资源元数据；实际数据是否开放取决于数据集许可和访问条件'}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('keyword')
    p.add_argument('--page', type=int, default=1)
    p.add_argument('--size', type=int, default=5)
    a = p.parse_args()
    print(json.dumps(search(a.keyword, a.page, a.size), ensure_ascii=False, indent=2))
if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(json.dumps({'error': str(e)}, ensure_ascii=False), file=sys.stderr)
        sys.exit(1)
