"""商务部数据中心全国社会消费品零售总额月度序列。"""
import release_runtime
import json
import re
import subprocess
from urllib.parse import urlencode
BASE = 'https://data.mofcom.gov.cn/datamofcom/front/gnmy/retail/GNMY01'
PAGE = 'https://data.mofcom.gov.cn/gnmy/monthSociety.shtml'

def _month(s):
    if not re.fullmatch('(19|20)\\d\\d(0[1-9]|1[0-2])', s):
        raise ValueError('月份需为 YYYYMM')
    return int(s[:4]) * 12 + int(s[4:])

def retail_months(start, end):
    a, b = (_month(start), _month(end))
    if b < a or b - a > 119:
        raise ValueError('时间顺序须正确，范围最多 120 个月')
    args = ['curl', '--fail', '--silent', '--show-error', '--max-time', '20', '--data', urlencode({'start_time': start, 'end_time': end}), BASE]
    payload = json.loads(release_runtime.run(args, check=True, capture_output=True).stdout)
    if not isinstance(payload, list):
        raise ValueError('数据结构改变')
    return {'source_url': PAGE, 'start': start, 'end': end, 'items': [{'month': x.get('month'), 'retail_100m_yuan': x.get('retail')} for x in payload if start <= str(x.get('month', '')) <= end], 'note': '单位亿元；上游未提供月份保留为空，不补零。'}

def retail_month(month):
    d = retail_months(month, month)
    matches = [x for x in d['items'] if x['month'] == month]
    if len(matches) != 1:
        raise ValueError('未找到该月的唯一数据，上游可能尚未发布或有修订')
    return {'source_url': PAGE, 'item': matches[0], 'note': d['note']}
