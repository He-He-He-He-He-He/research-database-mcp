"""Slovak Statistical Office STATdata: search and official open data download."""
import release_runtime
import argparse, io, json, re, time, zipfile
from urllib.parse import urlparse
import requests
BASE = 'https://statdata.statistics.sk/public/api/dc'

def _request(method, path, body=None, params=None):
    s = requests.Session()
    s.trust_env = False
    for attempt in range(3):
        try:
            r = s.request(method, BASE + path, json=body, params=params, timeout=40, stream=True)
            r.raise_for_status()
            break
        except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
            if attempt == 2:
                raise
            time.sleep(attempt + 1)
    parts = []
    size = 0
    for part in r.iter_content(65536):
        size += len(part)
        if size > 10000000:
            raise ValueError('响应超过 10 MB，请选择较小数据集')
        parts.append(part)
    return b''.join(parts)

def search(query, limit=10, page=0):
    if not isinstance(query, str) or not query.strip() or len(query) > 100 or (not 1 <= limit <= 50) or (not 0 <= page <= 1000):
        raise ValueError('搜索或分页参数无效')
    body = {'findText': query.strip(), 'pagingAndSorting': {'pageNumber': page, 'pageSize': limit}}
    value = json.loads(_request('POST', '/search/dataCube/EN', body))
    if not isinstance(value, dict) or not isinstance(value.get('content'), list):
        raise ValueError('搜索响应格式异常')
    return {'source': BASE + '/search/dataCube/EN', 'query': query, 'result': value, 'note': '目录更新时间、频率、地区来自统计局；仅有界搜索结果。'}

def data(cube, filters=None, limit=30):
    if not isinstance(cube, str) or not re.fullmatch('[A-Za-z0-9_]{1,40}', cube):
        raise ValueError('数据集代码无效')
    if not 1 <= limit <= 100:
        raise ValueError('limit 应为 1–100')
    filters = filters or {}
    if not isinstance(filters, dict) or len(filters) > 8 or any((not isinstance(k, str) or not isinstance(v, str) or len(k) > 120 or (len(v) > 200) for k, v in filters.items())):
        raise ValueError('筛选条件无效')
    body = {'dataCubePublicId': cube, 'lang': 'EN', 'type': 'JSON'}
    meta = json.loads(_request('POST', '/opendata/cube/dataset/download-url', body))
    url = meta.get('url', '')
    u = urlparse(url)
    expected = '/public/api/dc/opendata/cube/dataset/' + cube + '/download'
    if u.scheme != 'https' or u.hostname != 'statdata.statistics.sk' or u.path != expected:
        raise ValueError('官方返回的下载地址不符合预期')
    blob = _request('GET', '/opendata/cube/dataset/' + cube + '/download', params={'lang': 'EN', 'type': 'JSON'})
    z = zipfile.ZipFile(io.BytesIO(blob))
    members = [x for x in z.infolist() if not x.is_dir()]
    if len(members) != 1 or not members[0].filename.endswith('.json') or members[0].file_size > 25000000:
        raise ValueError('ZIP 内容不符合大小和文件类型限制')
    value = json.loads(z.read(members[0]))
    if not isinstance(value, list) or any((not isinstance(x, dict) for x in value)):
        raise ValueError('数据文件结构异常')
    if value and any((k not in value[0] for k in filters)):
        raise ValueError('筛选字段不在文件中')
    out = []
    count = 0
    for row in value:
        if any((str(row.get(k, '')) != v for k, v in filters.items())):
            continue
        count += 1
        if len(out) < limit:
            out.append(row)
    return {'source': url, 'cube': cube, 'filters': filters, 'total_matching_rows': count, 'shown': len(out), 'rows': out, 'note': '下载整个 JSON 压缩文件后本地筛选；保留指标、单位、时点及原值。字段和统计口径以该数据集官方说明为准。'}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    s = p.add_subparsers(dest='cmd', required=True)
    q = s.add_parser('search')
    q.add_argument('query')
    q.add_argument('--limit', type=int, default=10)
    q.add_argument('--page', type=int, default=0)
    q = s.add_parser('data')
    q.add_argument('cube')
    q.add_argument('--filters', default='{}')
    q.add_argument('--limit', type=int, default=30)
    a = p.parse_args()
    print(json.dumps(search(a.query, a.limit, a.page) if a.cmd == 'search' else data(a.cube, json.loads(a.filters), a.limit), ensure_ascii=False, indent=2))
if __name__ == '__main__':
    main()
