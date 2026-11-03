"""Official Taiwan public-library consolidated statistics, selected years."""
import release_runtime
import requests
URL = 'https://publibstat.nlpi.edu.tw/api/API/ConsolidationData'

def query(year, region=None, fields=None):
    year = int(year)
    if year < 2011 or year > 2100:
        raise ValueError('请输入合理的公历年份')
    r = requests.get(URL, params={'Year': year}, timeout=35)
    r.raise_for_status()
    rows = r.json()
    if not isinstance(rows, list):
        raise RuntimeError('接口未返回预期列表')
    if region is not None:
        rows = [row for row in rows if row.get('縣市別') == f'{year}-{region}']
    if fields is not None:
        if isinstance(fields, str):
            raise ValueError('fields 必须是字段名列表')
        rows = [{k: v for k, v in row.items() if k == '縣市別' or k in fields} for row in rows]
    return {'year': year, 'source_url': r.url, 'records': rows, 'count': len(rows), 'note': '保留原始字符串、单位和地区标签；部分地区另有“不含国立馆”行，不可相加。'}
