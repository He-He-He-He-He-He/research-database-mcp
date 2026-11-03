"""巴西 IBGE SIDRA 官方 values 接口，按已知统计表代码获取聚合数据。"""
import release_runtime
import argparse
import json
import re
import subprocess
from urllib.parse import quote
BASE = 'https://apisidra.ibge.gov.br/values'
MAX_BYTES = 10000000

def _digits(value, name):
    text = str(value)
    if not re.fullmatch('[0-9]{1,12}', text):
        raise ValueError(name + ' 须为数字代码')
    return text

def _codes(values, name):
    if not isinstance(values, list) or not values or len(values) > 20:
        raise ValueError(name + ' 须是 1–20 个代码组成的数组')
    out = [_digits(x, name) for x in values]
    if len(out) != len(set(out)):
        raise ValueError(name + ' 代码重复')
    return out

def observations(table, level, locations, variables, periods, classifications=None):
    table = _digits(table, '表')
    level = _digits(level, '地域层级')
    locations = _codes(locations, '地域')
    variables = _codes(variables, '变量')
    if periods == 'latest':
        periods_path = 'last%201'
        count_periods = 1
    else:
        periods_list = _codes(periods, '时期')
        periods_path = ','.join(periods_list)
        count_periods = len(periods_list)
    classifications = {} if classifications is None else classifications
    if not isinstance(classifications, dict) or len(classifications) > 5:
        raise ValueError('分类须为代码到类别数组的字典')
    count = len(locations) * len(variables) * count_periods
    extra = ''
    for code, values in classifications.items():
        c = _digits(code, '分类')
        category = _codes(values, '类别')
        count *= len(category)
        extra += '/c' + c + '/' + ','.join(category)
    if count > 1000:
        raise ValueError('单次选定组合最多 1000 条；未显式限制的分类也可能增加结果')
    path = '/t/' + table + '/n' + level + '/' + ','.join(locations) + '/v/' + ','.join(variables) + '/p/' + periods_path + extra
    url = BASE + path
    p = release_runtime.run(['/usr/bin/curl', '--fail', '--silent', '--show-error', '--compressed', '--max-time', '30', '--max-filesize', str(MAX_BYTES), url], capture_output=True, timeout=35)
    if p.returncode:
        raise RuntimeError('SIDRA 请求失败：' + p.stderr.decode('utf-8', 'replace')[:400])
    if len(p.stdout) > MAX_BYTES:
        raise ValueError('响应超过大小上限')
    data = json.loads(p.stdout)
    if not isinstance(data, list) or not data or (not isinstance(data[0], dict)) or ('V' not in data[0]):
        raise ValueError('上游结果格式异常')
    return {'source': url, 'header': data[0], 'rows': data[1:], 'returned': len(data) - 1, 'note': '保留葡语标题、地域与分类代码、单位以及 V 原始字符串和特殊标记。须核对表元数据、统计期间、含义及修订；非完整目录查询。'}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('table')
    p.add_argument('level')
    p.add_argument('--locations', required=True, help='数字代码逗号分隔')
    p.add_argument('--variables', required=True, help='数字代码逗号分隔')
    p.add_argument('--periods', required=True, help='时期数字代码逗号分隔，或 latest')
    p.add_argument('--classifications', default='{}', help='分类代码到类别代码数组的 JSON')
    a = p.parse_args()
    periods = 'latest' if a.periods == 'latest' else a.periods.split(',')
    print(json.dumps(observations(a.table, a.level, a.locations.split(','), a.variables.split(','), periods, json.loads(a.classifications)), ensure_ascii=False, indent=2))
if __name__ == '__main__':
    main()
