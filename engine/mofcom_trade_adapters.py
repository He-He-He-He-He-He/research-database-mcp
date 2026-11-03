"""商务部数据中心中国服务贸易月度统计，只读。"""
import release_runtime
import argparse, datetime, json, re, sys
from research import get
BASE = 'https://data.mofcom.gov.cn/datamofcom/front/fwmy/mouthly'

def _validate_month(v):
    if v and (not re.fullmatch('(19|20)\\d\\d(0[1-9]|1[0-2])', v)):
        raise ValueError('月份应为 YYYYMM')

def trade_list(start='', end='', page=1):
    _validate_month(start)
    _validate_month(end)
    if start and end and (start > end):
        raise ValueError('开始月份不可晚于结束月份')
    if not 1 <= page <= 100:
        raise ValueError('页码应在 1–100')
    d = get(BASE, {'start_date': start, 'end_date': end, 'pageNumber': page})
    if not isinstance(d.get('rows'), list):
        raise ValueError('服务贸易响应格式变化')
    return {'source': '商务部数据中心', 'source_url': 'https://data.mofcom.gov.cn/fwmy/monthly.shtml', 'start_month': start, 'end_month': end, 'page': page, 'total': d.get('total'), 'page_size': d.get('pageSize'), 'items': [{'month': x.get('mouth'), 'rmb_100m': {'total': x.get('importAndExportRMB'), 'exports': x.get('exportRMB'), 'imports': x.get('importRMB'), 'balance': x.get('differenceRMB')}, 'usd_100m': {'total': x.get('importAndExportUSD'), 'exports': x.get('exportUSD'), 'imports': x.get('importUSD'), 'balance': x.get('differenceUSD')}} for x in d['rows']], 'note': '金额单位分别为亿元人民币、亿美元；服务贸易非货物贸易，数值和更新以官方为准。'}

def trade_detail(month):
    _validate_month(month)
    if not month:
        raise ValueError('请输入月份 YYYYMM')
    d = trade_list(month, month, 1)
    matches = [x for x in d['items'] if x['month'] == month]
    if not matches:
        raise ValueError('未找到指定月份的数据')
    return {'source': d['source'], 'source_url': d['source_url'], 'item': matches[0], 'note': d['note']}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    s = p.add_subparsers(dest='cmd', required=True)
    q = s.add_parser('list')
    q.add_argument('--start', default='')
    q.add_argument('--end', default='')
    q.add_argument('--page', type=int, default=1)
    q = s.add_parser('detail')
    q.add_argument('month')
    a = p.parse_args()
    print(json.dumps(trade_list(a.start, a.end, a.page) if a.cmd == 'list' else trade_detail(a.month), ensure_ascii=False, indent=2))
if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(json.dumps({'error': str(e), 'note': '上游失败或结构变化，无自动重试'}, ensure_ascii=False), file=sys.stderr)
        sys.exit(1)
