"""世界银行 LPI 2.0 直接空运货物连接的伙伴经济体数。"""
import release_runtime
import argparse, json, re, subprocess
from urllib.parse import urlencode
BASE = 'https://data360api.worldbank.org/data360/data'

def air_cargo_partners(country, year):
    if not isinstance(country, str) or not re.fullmatch('[A-Z]{3}', country):
        raise ValueError('country 须为大写 ISO3 代码')
    if isinstance(year, bool) or not isinstance(year, int) or (not 2000 <= year <= 2100):
        raise ValueError('年份无效')
    dims = {'DATABASE_ID': 'WB_LPI_20', 'INDICATOR': 'AV_PRTN', 'REF_AREA': country}
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
    return {'source': 'World Bank Logistics Performance Indicators 2.0 via Data360', 'source_url': url, 'metadata_url': 'https://data360files.worldbank.org/data360-data/metadata/WB_LPI_20/AV_PRTN.pdf', 'country': country, 'year': year, 'unit': 'economies', 'scope': '直接空运货物连接的伙伴经济体数量，按年度独立来源地和目的地伙伴数的平均计算，因此可能有小数；数据为 Cargo iQ 跟踪样本，不是客运航线数，也不是伙伴经济体的并集计数。空值非零。', 'data': rows}
if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('country')
    p.add_argument('year', type=int)
    a = p.parse_args()
    print(json.dumps(air_cargo_partners(a.country, a.year), ensure_ascii=False, indent=2))
