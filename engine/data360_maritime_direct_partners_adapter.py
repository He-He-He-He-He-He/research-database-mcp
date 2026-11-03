"""世界银行 LPI 2.0 可直航的集装箱班轮经济体数量。"""
import release_runtime
import argparse, json, re, subprocess
from urllib.parse import urlencode
BASE = 'https://data360api.worldbank.org/data360/data'

def direct_partners(country, year):
    if not isinstance(country, str) or not re.fullmatch('[A-Z]{3}', country):
        raise ValueError('country 须为大写 ISO3 代码')
    if isinstance(year, bool) or not isinstance(year, int) or (not 2000 <= year <= 2100):
        raise ValueError('年份无效')
    dims = {'DATABASE_ID': 'WB_LPI_20', 'INDICATOR': 'CT_MC', 'REF_AREA': country}
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
    return {'source': 'World Bank Logistics Performance Indicators 2.0 via Data360', 'source_url': url, 'metadata_url': 'https://data360files.worldbank.org/data360-data/metadata/WB_LPI_20/CT_MC.pdf', 'country': country, 'year': year, 'unit': 'economies', 'scope': '某经济体通过集装箱定期班轮无需转运可直接连接的经济体数量，基于船舶追踪等数据，不是航线数、船只数或物流绩效调查评分。空值非零。', 'data': rows}
if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('country')
    p.add_argument('year', type=int)
    a = p.parse_args()
    print(json.dumps(direct_partners(a.country, a.year), ensure_ascii=False, indent=2))
