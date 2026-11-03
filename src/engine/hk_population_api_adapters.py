"""香港政府统计处公开 API：110-01001 按性别及年龄组别的人口。"""
import release_runtime
import argparse
import json
import re
import requests
API = 'https://www.censtatd.gov.hk/api/get.php'
DATASET = 'https://data.gov.hk/en-data/dataset/hk-censtatd-tablechart-110-01001'
TERMS = 'https://data.gov.hk/en/terms-and-conditions'

def population(period=None, sex=None, age=None):
    """返回官方表头、注释及符合条件的原始记录；None 表示不筛选，空字符串代表总计。"""
    if period is not None and (not re.fullmatch('\\d{4}(06|12)', str(period))):
        raise ValueError('period 应为 YYYY06 或 YYYY12')
    session = requests.Session()
    session.trust_env = False
    response = session.get(API, params={'id': '110-01001', 'lang': 'sc', 'full_series': '1'}, timeout=25)
    response.raise_for_status()
    payload = response.json()
    if payload.get('header', {}).get('status', {}).get('code') != 0 or not isinstance(payload.get('dataSet'), list):
        raise ValueError('统计处未返回预期数据')
    records = [r for r in payload['dataSet'] if (period is None or r.get('period') == str(period)) and (sex is None or r.get('SEX') == sex) and (age is None or r.get('AGE') == age)]
    return {'source': '香港特别行政区政府统计处 / DATA.GOV.HK', 'dataset_url': DATASET, 'api': API, 'terms': TERMS, 'table': '110-01001', 'header': payload['header'], 'filters': {'period': period, 'sex': sex, 'age': age}, 'matched': len(records), 'data': records}
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--period', help='例如 202606；缺省为全部时期')
    parser.add_argument('--sex', help='官方 SEX 代码；空字符串为总计')
    parser.add_argument('--age', help='官方 AGE 代码；空字符串为总计')
    args = parser.parse_args()
    print(json.dumps(population(args.period, args.sex, args.age), ensure_ascii=False, indent=2))
