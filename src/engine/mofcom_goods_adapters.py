"""商务部数据中心货物进出口月度统计，数据来源海关总署。"""
import release_runtime
import argparse, json, re, subprocess, sys
from urllib.parse import urlencode
BASE = 'https://data.mofcom.gov.cn/datamofcom/front/totalmonth/query'

def _month(v):
    if not re.fullmatch('(19|20)\\d\\d(0[1-9]|1[0-2])', v):
        raise ValueError('月份需为 YYYYMM')
    return int(v[:4]) * 12 + int(v[4:])

def goods_list(start, end):
    a = _month(start)
    b = _month(end)
    if b < a or b - a > 11:
        raise ValueError('时间顺序应正确，单次最多 12 个月')
    args = ['/usr/bin/curl', '--fail', '--silent', '--show-error', '--max-time', '25', '--data', urlencode({'startDate': start, 'endDate': end}), BASE]
    r = release_runtime.run(args, capture_output=True, text=True)
    if r.returncode:
        raise RuntimeError('上游查询失败（curl 状态 %d）' % r.returncode)
    try:
        d = json.loads(r.stdout)
    except json.JSONDecodeError:
        raise ValueError('上游未返回 JSON')
    if not isinstance(d, list) or not d or (not isinstance(d[0], list)):
        raise ValueError('上游返回结构改变')
    keys = ['trade_date', 'total_value', 'total_per', 'total_lj_value', 'imexgap_value', 'export_value', 'export_per', 'export_lj_value', 'import_value', 'import_per', 'import_lj_value']
    return {'source': '商务部数据中心，数据来源中国海关总署', 'source_url': 'https://data.mofcom.gov.cn/hwmy/imexmonth.shtml', 'start': start, 'end': end, 'items': [{k: x.get(k) for k in keys} for x in d[0]], 'note': '金额单位为亿美元，同比单位为百分比；lj 表示累计。未返回月份不自行补零，修订以官网为准。'}

def goods_detail(month):
    d = goods_list(month, month)
    items = [x for x in d['items'] if x['trade_date'] == month]
    if not items:
        raise ValueError('未找到该月')
    return {'source': d['source'], 'source_url': d['source_url'], 'item': items[0], 'note': d['note']}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    s = p.add_subparsers(dest='cmd', required=True)
    q = s.add_parser('list')
    q.add_argument('start')
    q.add_argument('end')
    q = s.add_parser('detail')
    q.add_argument('month')
    a = p.parse_args()
    print(json.dumps(goods_list(a.start, a.end) if a.cmd == 'list' else goods_detail(a.month), ensure_ascii=False, indent=2))
if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(json.dumps({'error': str(e), 'note': '上游失败或结构变化，无自动重试'}, ensure_ascii=False), file=sys.stderr)
        sys.exit(1)
