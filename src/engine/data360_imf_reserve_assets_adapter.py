"""IMF IRFCL 货币当局官方储备资产，月度美元计价。"""
import release_runtime
import argparse, json, re, subprocess
from urllib.parse import urlencode
BASE = 'https://data360api.worldbank.org/data360/data'

def reserve_assets(country, start, end):
    if not isinstance(country, str) or not re.fullmatch('[A-Z]{3}', country):
        raise ValueError('country 须为大写 ISO3 代码')
    for v in (start, end):
        if not isinstance(v, str) or not re.fullmatch('\\d{4}-(?:0[1-9]|1[0-2])', v):
            raise ValueError('月份应为 YYYY-MM')
    if start > end:
        raise ValueError('开始月份不得晚于结束月份')
    dims = {'DATABASE_ID': 'IMF_IRFCL', 'INDICATOR': 'IMF_IRFCL_RAFA', 'REF_AREA': country, 'SEX': '_T', 'AGE': '_T', 'URBANISATION': '_T', 'COMP_BREAKDOWN_1': '_Z', 'COMP_BREAKDOWN_2': 'IMF_SEC_MA', 'COMP_BREAKDOWN_3': '_Z', 'FREQ': 'M'}
    url = BASE + '?' + urlencode({**dims, 'timePeriodFrom': start, 'timePeriodTo': end})
    p = release_runtime.run(['curl', '--fail', '--silent', '--show-error', '--max-time', '25', url], capture_output=True, text=True, timeout=30)
    if p.returncode:
        raise RuntimeError('Data360 请求失败')
    d = json.loads(p.stdout)
    rows = d.get('value')
    if not isinstance(d.get('count'), int) or not isinstance(rows, list) or d['count'] != len(rows):
        raise RuntimeError('Data360 数据数量异常')
    if any((any((r.get(k) != v for k, v in dims.items())) or r.get('UNIT_MEASURE') != 'USD' or r.get('UNIT_MULT') != 6 for r in rows)):
        raise RuntimeError('Data360 维度或单位不匹配')
    return {'source': 'IMF International Reserves and Foreign Currency Liquidity via World Bank Data360', 'source_url': url, 'metadata_url': 'https://data360files.worldbank.org/data360-data/metadata/IMF_IRFCL/IMF_IRFCL_RAFA.pdf', 'country': country, 'unit': 'million USD', 'scope': '货币当局官方储备资产总额，按月、百万美元，不等于仅外汇储备；储备资产还包括黄金、SDR 等。Data360 此数据集可能滞后，非实时值，原始状态及单位乘数保留。空结果不表示零。', 'count': len(rows), 'data': rows}
if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('country')
    p.add_argument('start')
    p.add_argument('end')
    a = p.parse_args()
    print(json.dumps(reserve_assets(a.country, a.start, a.end), ensure_ascii=False, indent=2))
