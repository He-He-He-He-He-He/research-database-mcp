"""香港金融管理局正式开放 API：日汇率及经济统计。"""
import release_runtime
import argparse
import datetime as dt
import json
import re
import requests
ROOT = 'https://api.hkma.gov.hk/public/market-data-and-statistics/monthly-statistical-bulletin/'
DOCS = 'https://apidocs.hkma.gov.hk/documentation/'
DATASETS = {'exchange': ('er-ir/er-eeri-daily', 'end_of_day', 'https://apidocs.hkma.gov.hk/documentation/market-data-and-statistics/monthly-statistical-bulletin/er-ir/er-eeri-daily/'), 'economy': ('financial/economic-statistics', 'end_of_month', 'https://apidocs.hkma.gov.hk/documentation/market-data-and-statistics/monthly-statistical-bulletin/financial/economic-statistics/')}

def query(dataset, start=None, end=None, limit=20, offset=0):
    if dataset not in DATASETS:
        raise ValueError('dataset 仅支持 exchange 或 economy')
    if not isinstance(limit, int) or not 1 <= limit <= 1000 or (not isinstance(offset, int)) or (offset < 0):
        raise ValueError('limit 为 1–1000，offset 为非负整数')
    path, field, detail = DATASETS[dataset]
    for value in (start, end):
        if value is not None:
            pattern = '\\d{4}-\\d{2}-\\d{2}' if dataset == 'exchange' else '\\d{4}-\\d{2}'
            if not re.fullmatch(pattern, value):
                raise ValueError('日期格式不正确')
            dt.date.fromisoformat(value if dataset == 'exchange' else value + '-01')
    if start and end and (start > end):
        raise ValueError('开始日期不得晚于结束日期')
    params = {'pagesize': limit, 'offset': offset, 'sortby': field, 'sortorder': 'desc'}
    if start or end:
        params['choose'] = field
        if start:
            params['from'] = start
        if end:
            params['to'] = end
    r = requests.get(ROOT + path, params=params, timeout=25)
    r.raise_for_status()
    j = r.json()
    if j.get('header', {}).get('success') is not True or not isinstance(j.get('result', {}).get('records'), list):
        raise ValueError('香港金管局 API 返回错误')
    return {'source': '香港金融管理局 Open API', 'api': ROOT + path, 'documentation': detail, 'parameters': params, 'returned': j['result'].get('datasize'), 'records': j['result']['records']}
if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('dataset', choices=DATASETS)
    p.add_argument('--start')
    p.add_argument('--end')
    p.add_argument('--limit', type=int, default=20)
    p.add_argument('--offset', type=int, default=0)
    a = p.parse_args()
    print(json.dumps(query(a.dataset, a.start, a.end, a.limit, a.offset), ensure_ascii=False, indent=2))
