"""新加坡政府 data.gov.sg 数据集目录、元数据和表格首屏。"""
import release_runtime
import argparse
import json
import re
import subprocess
from urllib.parse import urlencode
BASE = 'https://api-production.data.gov.sg/v2/public/api/datasets'
MAX_BYTES = 8000000

def _id(value):
    if not isinstance(value, str) or not re.fullmatch('d_[0-9a-f]{32}', value):
        raise ValueError('数据集 ID 无效')
    return value

def _get(path='', params=None):
    url = BASE + path + ('?' + urlencode(params) if params else '')
    p = release_runtime.run(['/usr/bin/curl', '--fail', '--silent', '--show-error', '--compressed', '--max-time', '30', '--max-filesize', str(MAX_BYTES), url], capture_output=True, timeout=35)
    if p.returncode:
        raise RuntimeError('data.gov.sg 请求失败：' + p.stderr.decode('utf-8', 'replace')[:400])
    if len(p.stdout) > MAX_BYTES:
        raise ValueError('响应超过大小限制')
    value = json.loads(p.stdout)
    if not isinstance(value, dict) or value.get('code') != 0 or (not isinstance(value.get('data'), dict)):
        raise ValueError('上游返回失败或结构异常')
    return (url, value['data'])

def datasets(page=1, keyword=''):
    if isinstance(page, bool) or not isinstance(page, int) or (not 1 <= page <= 10000):
        raise ValueError('页码无效')
    if not isinstance(keyword, str) or len(keyword) > 150:
        raise ValueError('关键词无效')
    url, v = _get('', {'page': page})
    items = v.get('datasets')
    if not isinstance(items, list):
        raise ValueError('目录返回异常')
    found = [x for x in items if keyword.casefold() in str(x.get('name', '')).casefold()]
    return {'source': url, 'page': page, 'pages': v.get('pages'), 'page_items': len(items), 'matched': len(found), 'items': found, 'note': '关键词只筛选指定目录页，非全站搜索；目录含多个政府机构及非统计数据。'}

def metadata(dataset):
    url, data = _get('/' + _id(dataset) + '/metadata')
    if data.get('datasetId') != dataset:
        raise ValueError('元数据编号不匹配')
    return {'source': url, 'metadata': data, 'note': '字段、来源、覆盖期与说明来自官方目录；非所有格式都支持行 API。'}

def first_rows(dataset, limit=20):
    if isinstance(limit, bool) or not isinstance(limit, int) or (not 1 <= limit <= 100):
        raise ValueError('limit 须为 1–100')
    url, data = _get('/' + _id(dataset) + '/list-rows', {'limit': limit})
    if data.get('datasetId') != dataset or not isinstance(data.get('rows'), list):
        raise ValueError('行数据格式异常')
    return {'source': url, 'dataset': dataset, 'data': data, 'note': '仅返回首屏，不能当全量；上游提供 next 但实测部分数据集游标未前进，此适配器不提供后续分页。字段值通常为字符串，须核对数据集来源、时间和单位。'}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    s = p.add_subparsers(dest='cmd', required=True)
    q = s.add_parser('datasets')
    q.add_argument('--page', type=int, default=1)
    q.add_argument('--keyword', default='')
    q = s.add_parser('metadata')
    q.add_argument('dataset')
    q = s.add_parser('first')
    q.add_argument('dataset')
    q.add_argument('--limit', type=int, default=20)
    a = p.parse_args()
    v = datasets(a.page, a.keyword) if a.cmd == 'datasets' else metadata(a.dataset) if a.cmd == 'metadata' else first_rows(a.dataset, a.limit)
    print(json.dumps(v, ensure_ascii=False, indent=2))
if __name__ == '__main__':
    main()
