"""商务部数据中心外商直接投资与非金融类对外直接投资。"""
import release_runtime
import json
import re
import subprocess
from urllib.parse import urlencode
ROOT = 'https://data.mofcom.gov.cn/datamofcom/front/'
CONFIG = {'inbound': ('lywz/direct/query', 'startDate', 'endDate', 'data_time', 'https://data.mofcom.gov.cn/lywz/inmr.shtml'), 'outbound': ('tzhz/fordirinvest/dateQuery', 'start_date', 'end_date', 'time', 'https://data.mofcom.gov.cn/tzhz/fordirinvest.shtml')}

def _validate(month):
    if not re.fullmatch('(19|20)\\d\\d(0[1-9]|1[0-2])', month):
        raise ValueError('月份需为 YYYYMM')
    return int(month[:4]) * 12 + int(month[4:])

def investment_list(kind, start, end):
    if kind not in CONFIG:
        raise ValueError('kind 应为 inbound 或 outbound')
    a, b = (_validate(start), _validate(end))
    if b < a or b - a > 119:
        raise ValueError('时间顺序须正确，范围最多 120 个月')
    path, k1, k2, key, url = CONFIG[kind]
    args = ['curl', '--fail', '--silent', '--show-error', '--max-time', '20', '--data', urlencode({k1: start, k2: end}), ROOT + path]
    data = json.loads(release_runtime.run(args, check=True, capture_output=True).stdout)
    if not isinstance(data, list) or not data or (not isinstance(data[0], list)):
        raise ValueError('上游返回结构变化')
    items = [x for x in data[0] if start <= str(x.get(key, '')) <= end]
    note = '新设外商投资企业数为年初至当月累计、同比为百分比；实际使用外资金额列单位亿美元，短横线为缺失。' if kind == 'inbound' else '年初至当月累计非金融类对外直接投资；non_financial 单位亿美元，yoy 为美元口径同比百分比，country 为国家地区数，num_enterprice 为境外企业数。'
    return {'source_url': url, 'kind': kind, 'start': start, 'end': end, 'items': items, 'note': note}

def investment_detail(kind, month):
    result = investment_list(kind, month, month)
    key = CONFIG[kind][3]
    rows = [x for x in result['items'] if x.get(key) == month]
    if len(rows) != 1:
        raise ValueError('未找到唯一月份数据')
    return {'source_url': result['source_url'], 'kind': kind, 'month': month, 'item': rows[0], 'note': result['note']}
