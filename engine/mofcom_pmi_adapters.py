"""商务部数据中心月度采购经理人指数序列。"""
import release_runtime
import json
import re
import subprocess
from urllib.parse import urlencode
BASE = 'https://data.mofcom.gov.cn/datamofcom/front/zhtj/dateQuery'
PAGE = 'https://data.mofcom.gov.cn/zhtj/pmi.shtml'

def _month(v):
    if not re.fullmatch('(19|20)\\d\\d(0[1-9]|1[0-2])', v):
        raise ValueError('月份需为 YYYYMM')
    return int(v[:4]) * 12 + int(v[4:])

def pmi_list(start, end):
    a, b = (_month(start), _month(end))
    if b < a or b - a > 119:
        raise ValueError('时间顺序须正确，范围最多 120 个月')
    args = ['curl', '--fail', '--silent', '--show-error', '--max-time', '20', '--data', urlencode({'start_date': start, 'end_date': end, 'type': '6', 'module_no': '046'}), BASE]
    d = json.loads(release_runtime.run(args, check=True, capture_output=True).stdout)
    if not isinstance(d, list) or not d or (not isinstance(d[0], list)):
        raise ValueError('上游返回格式变化')
    return {'source_url': PAGE, 'start': start, 'end': end, 'items': [x for x in d[0] if start <= str(x.get('time_view', '')) <= end], 'note': '月度指数，单位%；官网该序列未明确细分类别，应核对当期国家统计局数据。缺失不补零。'}

def pmi_detail(month):
    result = pmi_list(month, month)
    matches = [x for x in result['items'] if x.get('time_view') == month]
    if len(matches) != 1:
        raise ValueError('未找到该月唯一数据')
    return {'source_url': PAGE, 'item': matches[0], 'note': result['note']}
