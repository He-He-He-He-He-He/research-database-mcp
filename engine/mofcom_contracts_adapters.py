"""商务部数据中心全国对外承包工程累计统计。"""
import release_runtime
import json
import re
import subprocess
from urllib.parse import urlencode
BASE = 'https://data.mofcom.gov.cn/datamofcom/front/tzhz/forEngineerStac/dateQuery'
PAGE = 'https://data.mofcom.gov.cn/tzhz/forengineerstac.shtml'

def _month(month):
    if not re.fullmatch('(19|20)\\d\\d(0[1-9]|1[0-2])', month):
        raise ValueError('月份需为 YYYYMM')
    return int(month[:4]) * 12 + int(month[4:])

def contracts_list(start, end):
    a, b = (_month(start), _month(end))
    if b < a or b - a > 119:
        raise ValueError('时间顺序须正确，范围最多 120 个月')
    args = ['curl', '--fail', '--silent', '--show-error', '--max-time', '20', '--data', urlencode({'start_date': start, 'end_date': end}), BASE]
    data = json.loads(release_runtime.run(args, check=True, capture_output=True).stdout)
    if not isinstance(data, list) or not data or (not isinstance(data[0], list)):
        raise ValueError('上游返回结构变化')
    items = [x for x in data[0] if start <= str(x.get('project_time', '')) <= end]
    return {'source_url': PAGE, 'start': start, 'end': end, 'items': items, 'note': '年初至当月累计金额，单位亿美元，同比为美元口径百分比；空值不补零。'}

def contracts_detail(month):
    data = contracts_list(month, month)
    matches = [x for x in data['items'] if x.get('project_time') == month]
    if len(matches) != 1:
        raise ValueError('未找到唯一月份数据')
    return {'source_url': PAGE, 'item': matches[0], 'note': data['note']}
