"""世界银行 LPI 2.0 国际邮政连接伙伴数（万国邮联数据）。"""
import release_runtime
import argparse, json, re, subprocess
from urllib.parse import urlencode
BASE = 'https://data360api.worldbank.org/data360/data'
CODES = {'b2b': 'PC_B2B', 'b2c': 'PC_B2C'}

def postal_partners(country, year, kind='b2b'):
    if not isinstance(country, str) or not re.fullmatch('[A-Z]{3}', country):
        raise ValueError('country 须为大写 ISO3 代码')
    if isinstance(year, bool) or not isinstance(year, int) or (not 2000 <= year <= 2100):
        raise ValueError('年份无效')
    if kind not in CODES:
        raise ValueError('kind 须为 b2b 或 b2c')
    dims = {'DATABASE_ID': 'WB_LPI_20', 'INDICATOR': CODES[kind], 'REF_AREA': country}
    url = BASE + '?' + urlencode({**dims, 'timePeriodFrom': year, 'timePeriodTo': year})
    p = release_runtime.run(['curl', '--fail', '--silent', '--show-error', '--max-time', '25', url], capture_output=True, text=True, timeout=30)
    if p.returncode:
        raise RuntimeError('Data360 请求失败')
    d = json.loads(p.stdout)
    rows = d.get('value')
    if not isinstance(d.get('count'), int) or not isinstance(rows, list) or d['count'] != len(rows) or (len(rows) > 1):
        raise RuntimeError('Data360 数据数量异常')
    if any((any((r.get(k) != v for k, v in dims.items())) or r.get('TIME_PERIOD') != str(year) or r.get('UNIT_MEASURE') != 'PRTN' or (r.get('UNIT_MULT') != 0) or (r.get('FREQ') != 'A') for r in rows)):
        raise RuntimeError('Data360 维度或单位不匹配')
    return {'source': 'Universal Postal Union via World Bank LPI 2.0 / Data360', 'source_url': url, 'metadata_url': 'https://data360files.worldbank.org/data360-data/metadata/WB_LPI_20/' + CODES[kind] + '.pdf', 'country': country, 'year': year, 'kind': kind, 'unit': 'partner economies, average', 'scope': '国际邮政连接伙伴数为年度独立来源地和目的地伙伴数的平均，可能有小数；B2B 按包裹（至少 2kg）与 EMS 邮类近似，B2C 按信件及至多 2kg 小包邮类近似，并非实际交易主体识别。数据来自万国邮联 PREDES，空值不是零。', 'data': rows}
if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('country')
    p.add_argument('year', type=int)
    p.add_argument('--kind', choices=CODES, default='b2b')
    a = p.parse_args()
    print(json.dumps(postal_partners(a.country, a.year, a.kind), ensure_ascii=False, indent=2))
