"""商务部对外劳务合作累计派出人员统计。"""
import release_runtime
import json
import re
import subprocess
from urllib.parse import urlencode
BASE = 'https://data.mofcom.gov.cn/datamofcom/front/tzhz/forLaborCooper/dateQuery'
PAGE = 'https://data.mofcom.gov.cn/tzhz/forlaborcoop.shtml'

def _month(month):
    if not re.fullmatch('(19|20)\\d\\d(0[1-9]|1[0-2])', month):
        raise ValueError('月份需为 YYYYMM')
    return int(month[:4]) * 12 + int(month[4:])

def overseas_labor_list(start, end):
    a, b = (_month(start), _month(end))
    if b < a or b - a > 119:
        raise ValueError('时间顺序须正确，范围最多 120 个月')
    args = ['curl', '--fail', '--silent', '--show-error', '--max-time', '20', '--data', urlencode({'start_date': start, 'end_date': end}), BASE]
    data = json.loads(release_runtime.run(args, check=True, capture_output=True).stdout)
    if not isinstance(data, list) or not data or (not isinstance(data[0], list)):
        raise ValueError('上游返回结构变化')
    return {'source_url': PAGE, 'start': start, 'end': end, 'items': [x for x in data[0] if start <= str(x.get('time', '')) <= end], 'note': '均为年初至当月累计派出人数或较上年同期增加人数，单位万人；num_yoy 是增加人数，不是增长率；缺失不补零。'}

def overseas_labor_detail(month):
    data = overseas_labor_list(month, month)
    matches = [x for x in data['items'] if x.get('time') == month]
    if len(matches) != 1:
        raise ValueError('未找到唯一月份数据')
    return {'source_url': PAGE, 'item': matches[0], 'note': data['note']}
