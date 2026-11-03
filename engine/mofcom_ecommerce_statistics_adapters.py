"""全国电子商务公共服务网季度数据查询（各数据行保留原期次）。"""
import release_runtime
import argparse
import json
import re
import subprocess
from urllib.parse import urlencode
BASE = 'https://dzswgf.mofcom.gov.cn/ecps/api/'
PAGE = 'https://dzswgf.mofcom.gov.cn/m_sjcx.html'

def request(endpoint, params=None):
    url = BASE + endpoint + ('?' + urlencode(params) if params else '')
    return release_runtime.run(['curl', '--fail', '--silent', '--show-error', '--location', '--max-time', '20', url], check=True, capture_output=True, text=True).stdout

def latest():
    result = request('lastDate').strip()
    if not re.fullmatch('20\\d{2}Q[1-4]', result):
        raise ValueError('上游最新期次格式异常')
    return {'latest_period': result, 'source': PAGE}

def data(period, keyword=''):
    if not re.fullmatch('20\\d{2}Q[1-4]', period) or int(period[:4]) < 2015:
        raise ValueError('period 格式为 2015Q1 起的 YYYYQ1—YYYYQ4')
    raw = json.loads(request('datasearch', {'dataMonth': period}))
    if not isinstance(raw, list) or any((not isinstance(x, dict) or 'indication' not in x or 'dataMonth' not in x for x in raw)):
        raise ValueError('上游数据格式异常')
    rows = [x for x in raw if keyword in str(x.get('indication') or '')]
    return {'requested_period': period, 'period_explanation': {'Q1': '第一季度', 'Q2': '半年度', 'Q3': '前三季度', 'Q4': '全年度'}[period[-2:]], 'source': PAGE, 'keyword': keyword, 'items': rows, 'note': '保留上游每行 dataMonth、单位、数据来源和 null；部分行的实际期次可能是具体月份。'}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    s = p.add_subparsers(dest='cmd', required=True)
    s.add_parser('latest')
    d = s.add_parser('data')
    d.add_argument('period')
    d.add_argument('--keyword', default='')
    a = p.parse_args()
    print(json.dumps(latest() if a.cmd == 'latest' else data(a.period, a.keyword), ensure_ascii=False, indent=2))
if __name__ == '__main__':
    main()
