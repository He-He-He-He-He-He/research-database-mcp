"""商务部数据中心年度国内生产总值。"""
import release_runtime
import json
import re
import subprocess
from urllib.parse import urlencode
BASE = 'https://data.mofcom.gov.cn/datamofcom/front/zhtj/gdp/dateQuery'
PAGE = 'https://data.mofcom.gov.cn/zhtj/gdp.shtml'

def gdp_list(start, end):
    if not re.fullmatch('(19|20)\\d{2}', start) or not re.fullmatch('(19|20)\\d{2}', end) or int(end) < int(start) or (int(end) - int(start) > 100):
        raise ValueError('请输入合理的年份范围')
    args = ['curl', '--fail', '--silent', '--show-error', '--max-time', '20', '--data', urlencode({'start_date': start, 'end_date': end, 'type': '1'}), BASE]
    data = json.loads(release_runtime.run(args, check=True, capture_output=True).stdout)
    if not isinstance(data, list) or not data or (not isinstance(data[0], list)):
        raise ValueError('上游返回结构变化')
    return {'source_url': PAGE, 'start_year': start, 'end_year': end, 'items': [x for x in data[0] if start <= str(x.get('time_view', '')) <= end], 'note': '年度国内生产总值，单位亿元；未返回年份不补零，数值可能修订。'}

def gdp_detail(year):
    result = gdp_list(year, year)
    matches = [x for x in result['items'] if x.get('time_view') == year]
    if len(matches) != 1:
        raise ValueError('未找到唯一的年度数据')
    return {'source_url': PAGE, 'item': matches[0], 'note': result['note']}
