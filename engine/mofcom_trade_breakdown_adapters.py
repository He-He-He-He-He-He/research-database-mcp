"""商务部数据中心货物进出口分国家地区、贸易方式统计。"""
import release_runtime
import json
import re
import subprocess
from urllib.parse import urlencode
ROOT = 'https://data.mofcom.gov.cn/datamofcom/front/'
PAGES = {'country': 'https://data.mofcom.gov.cn/hwmy/imexCountry.shtml', 'method': 'https://data.mofcom.gov.cn/hwmy/imexTradeMethod.shtml'}

def _query(kind, month):
    if not re.fullmatch('(19|20)\\d\\d(0[1-9]|1[0-2])', month):
        raise ValueError('月份需为 YYYYMM')
    path, param = {'country': ('totalbycountry/query', 'date'), 'method': ('totaltrademethod/query', 'query_date')}[kind]
    r = release_runtime.run(['curl', '--fail', '--silent', '--show-error', '--max-time', '20', '--data', urlencode({param: month}), ROOT + path], check=True, capture_output=True)
    data = json.loads(r.stdout)
    if kind == 'country':
        if not isinstance(data, dict) or not isinstance(data.get('rows'), list):
            raise ValueError('上游数据结构变化')
        rows = data['rows']
    else:
        if not isinstance(data, list) or any((not isinstance(group, list) for group in data)):
            raise ValueError('上游数据结构变化')
        rows = [row for group in data for row in group]
    return [r for r in rows if r.get('trade_date') == month]

def trade_country_list(month, keyword=''):
    rows = [r for r in _query('country', month) if keyword in str(r.get('type', ''))]
    return {'source_url': PAGES['country'], 'month': month, 'items': rows, 'note': '此表为累计金额，单位亿美元，同比%；仅上游列示的国家地区，空值非零。'}

def trade_country_detail(month, name):
    x = trade_country_list(month, name)
    rows = [r for r in x['items'] if r.get('type') == name]
    if len(rows) != 1:
        raise ValueError('未找到唯一的国家或地区')
    return {'source_url': PAGES['country'], 'month': month, 'item': rows[0], 'note': x['note']}

def trade_method_list(month):
    return {'source_url': PAGES['method'], 'month': month, 'items': _query('method', month), 'note': '金额为亿美元；包含当月和累计字段，同比为%；空值或短横线不等于零。'}

def trade_method_detail(month, name):
    x = trade_method_list(month)
    rows = [r for r in x['items'] if r.get('type') == name]
    if len(rows) != 1:
        raise ValueError('未找到唯一贸易方式')
    return {'source_url': PAGES['method'], 'month': month, 'item': rows[0], 'note': x['note']}
