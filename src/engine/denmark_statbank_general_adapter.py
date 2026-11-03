"""丹麦统计局 StatBank 主题、表元数据及有界数据查询。"""
import release_runtime
import argparse
import json
import re
import subprocess
BASE = 'https://api.statbank.dk/v1/'
MAX_BYTES = 12000000

def _request(endpoint, body):
    if endpoint not in ('subjects', 'tables', 'tableinfo', 'data'):
        raise ValueError('无效操作')
    data = json.dumps(body, ensure_ascii=False).encode('utf-8')
    p = release_runtime.run(['/usr/bin/curl', '--fail', '--silent', '--show-error', '--compressed', '--max-time', '35', '--max-filesize', str(MAX_BYTES), '-H', 'Content-Type: application/json', '--data-binary', '@-', BASE + endpoint], input=data, capture_output=True, timeout=40)
    if p.returncode:
        raise RuntimeError('丹麦 StatBank 请求失败：' + p.stderr.decode('utf-8', 'replace')[:400])
    if len(p.stdout) > MAX_BYTES:
        raise ValueError('响应超过大小上限')
    return json.loads(p.stdout)

def subjects(subject=''):
    if not isinstance(subject, str) or not re.fullmatch('[0-9]{0,15}', subject):
        raise ValueError('主题代码无效')
    body = {'lang': 'en', 'format': 'JSON'}
    if subject:
        body['subjects'] = [subject]
    value = _request('subjects', body)
    if not isinstance(value, list):
        raise ValueError('主题数据格式异常')
    return {'source': BASE + 'subjects', 'query': body, 'items': value, 'note': '仅返回当前层级；主题与内容可能由官方更新。'}

def tables(subject, keyword=''):
    if not isinstance(subject, str) or not re.fullmatch('[0-9]{1,15}', subject):
        raise ValueError('须先指定主题代码')
    if not isinstance(keyword, str) or len(keyword) > 150:
        raise ValueError('关键词无效')
    body = {'lang': 'en', 'format': 'JSON', 'subjects': [subject]}
    value = _request('tables', body)
    if not isinstance(value, list):
        raise ValueError('统计表目录格式异常')
    rows = [x for x in value if keyword.casefold() in (str(x.get('id', '')) + ' ' + str(x.get('text', ''))).casefold()]
    return {'source': BASE + 'tables', 'subject': subject, 'keyword': keyword, 'total_in_subject': len(value), 'matched': len(rows), 'items': rows, 'note': '关键词在所选主题返回的表标题和代码中本地匹配，不是全库搜索。'}

def _table(table):
    if not isinstance(table, str) or not re.fullmatch('[A-Za-z0-9_]{1,30}', table):
        raise ValueError('无效表编号')
    return table

def metadata(table):
    body = {'lang': 'en', 'format': 'JSON', 'table': _table(table)}
    value = _request('tableinfo', body)
    if not isinstance(value, dict) or not isinstance(value.get('variables'), list):
        raise ValueError('元数据格式异常')
    return {'source': BASE + 'tableinfo', 'request': body, 'metadata': value, 'note': '单位、口径、时间、可选择代码和注释以此元数据为准。'}

def data(table, selections):
    info = metadata(table)['metadata']
    variables = info['variables']
    ids = [v['id'] for v in variables]
    if not isinstance(selections, dict) or set(selections) != set(ids):
        raise ValueError('须显式指定所有变量：' + ', '.join(ids))
    cells = 1
    query = []
    for var in variables:
        code = var['id']
        values = selections[code]
        valid = {x['id'] for x in var['values']}
        if not isinstance(values, list) or not values or len(values) > 100 or any((not isinstance(x, str) or x not in valid for x in values)) or (len(values) != len(set(values))):
            raise ValueError('变量 ' + code + ' 取值无效，参见元数据')
        cells *= len(values)
        if cells > 5000:
            raise ValueError('单次查询最多 5000 个观测组合')
        query.append({'code': code, 'values': values})
    body = {'lang': 'en', 'table': _table(table), 'format': 'JSONSTAT', 'variables': query}
    value = _request('data', body)
    if not isinstance(value, dict) or not isinstance(value.get('dataset'), dict) or 'value' not in value['dataset']:
        raise ValueError('未识别 JSON-stat 数据')
    return {'source': BASE + 'data', 'request': body, 'metadata': info, 'requested_combinations': cells, 'data': value, 'note': '保留 JSON-stat 原始维度、单位和状态；不指定维度时上游可能自动汇总，因此本工具要求显式指定全部维度。'}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    s = p.add_subparsers(dest='cmd', required=True)
    q = s.add_parser('subjects')
    q.add_argument('subject', nargs='?', default='')
    q = s.add_parser('tables')
    q.add_argument('subject')
    q.add_argument('--keyword', default='')
    q = s.add_parser('metadata')
    q.add_argument('table')
    q = s.add_parser('data')
    q.add_argument('table')
    q.add_argument('--selections', required=True)
    a = p.parse_args()
    res = subjects(a.subject) if a.cmd == 'subjects' else tables(a.subject, a.keyword) if a.cmd == 'tables' else metadata(a.table) if a.cmd == 'metadata' else data(a.table, json.loads(a.selections))
    print(json.dumps(res, ensure_ascii=False, indent=2))
if __name__ == '__main__':
    main()
