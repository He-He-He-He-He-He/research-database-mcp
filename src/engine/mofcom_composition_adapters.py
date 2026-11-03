"""商务部数据中心：海关货物进出口商品构成。"""
import release_runtime
import json
import re
import subprocess
from urllib.parse import urlencode
BASE = 'https://data.mofcom.gov.cn/datamofcom/front/composition/query'
PAGE = 'https://data.mofcom.gov.cn/hwmy/composition.shtml'

def composition_list(month, keyword=''):
    if not re.fullmatch('(19|20)\\d\\d(0[1-9]|1[0-2])', month):
        raise ValueError('月份需为 YYYYMM')
    r = release_runtime.run(['curl', '--fail', '--silent', '--show-error', '--max-time', '20', '--data', urlencode({'date': month}), BASE], check=True, capture_output=True)
    payload = json.loads(r.stdout)
    if not isinstance(payload, dict) or not isinstance(payload.get('rows'), list):
        raise ValueError('上游数据格式变化')
    rows = [x for x in payload['rows'] if x.get('data_time') == month and keyword in str(x.get('name', ''))]
    return {'month': month, 'source_url': PAGE, 'items': rows, 'note': '金额单位千美元，累计同比单位%；原分类含总值、类、章等不同层级，不可直接相加。'}

def composition_detail(month, name):
    d = composition_list(month, name)
    matches = [x for x in d['items'] if x.get('name') == name]
    if len(matches) != 1:
        raise ValueError('没有唯一匹配的分类名称')
    return {'month': month, 'source_url': PAGE, 'item': matches[0], 'note': d['note']}
