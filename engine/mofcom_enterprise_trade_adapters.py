"""商务部数据中心货物进出口分企业性质统计。"""
import release_runtime
import json
import re
import subprocess
from urllib.parse import urlencode
BASE = 'https://data.mofcom.gov.cn/datamofcom/front/totalcomtype/query'
PAGE = 'https://data.mofcom.gov.cn/hwmy/imexComType.shtml'

def enterprise_trade_list(month):
    if not re.fullmatch('(19|20)\\d\\d(0[1-9]|1[0-2])', month):
        raise ValueError('月份需为 YYYYMM')
    args = ['curl', '--fail', '--silent', '--show-error', '--max-time', '20', '--data', urlencode({'query_date': month}), BASE]
    data = json.loads(release_runtime.run(args, check=True, capture_output=True).stdout)
    if not isinstance(data, list) or any((not isinstance(group, list) for group in data)):
        raise ValueError('上游返回结构变化')
    rows = [row for group in data for row in group if row.get('trade_date') == month]
    return {'source_url': PAGE, 'month': month, 'items': rows, 'note': '金额单位亿美元、同比%；仅列示该月数据，空值和短横线不是零。'}

def enterprise_trade_detail(month, name):
    d = enterprise_trade_list(month)
    matches = [x for x in d['items'] if x.get('type') == name]
    if len(matches) != 1:
        raise ValueError('未找到唯一匹配的企业性质')
    return {'source_url': PAGE, 'month': month, 'item': matches[0], 'note': d['note']}
