"""联合国仙台框架多国灾害死亡及失踪人数比例。"""
import release_runtime
import argparse, json, re, subprocess
from urllib.parse import urlencode
BASE = 'https://data360api.worldbank.org/data360/data'

def disaster_mortality(country, start, end):
    if not isinstance(country, str) or not re.fullmatch('[A-Z]{3}', country):
        raise ValueError('country 须为大写 ISO3 代码')
    if any((isinstance(x, bool) or not isinstance(x, int) for x in (start, end))) or not 1900 <= start <= end <= 2100:
        raise ValueError('年份范围无效')
    dims = {'DATABASE_ID': 'UNDRR_SFM', 'INDICATOR': 'UNDRR_SFM_A1', 'REF_AREA': country, 'SEX': '_Z', 'AGE': '_Z', 'URBANISATION': '_Z', 'COMP_BREAKDOWN_1': '_T', 'COMP_BREAKDOWN_2': '_Z', 'COMP_BREAKDOWN_3': '_Z', 'FREQ': 'A'}
    url = BASE + '?' + urlencode({**dims, 'timePeriodFrom': start, 'timePeriodTo': end})
    p = release_runtime.run(['curl', '--fail', '--silent', '--show-error', '--max-time', '25', url], capture_output=True, text=True, timeout=30)
    if p.returncode:
        raise RuntimeError('Data360 请求失败')
    d = json.loads(p.stdout)
    rows = d.get('value')
    if not isinstance(d.get('count'), int) or not isinstance(rows, list) or d['count'] != len(rows):
        raise RuntimeError('Data360 数据数量异常')
    if any((any((r.get(k) != v for k, v in dims.items())) or r.get('UNIT_MEASURE') not in ('10P5PS', 'PS') or r.get('UNIT_MULT') != 0 for r in rows)):
        raise RuntimeError('Data360 维度或单位不匹配')
    selected = [r for r in rows if r['UNIT_MEASURE'] == '10P5PS']
    return {'source': 'UNDRR Sendai Framework Monitor via World Bank Data360', 'source_url': url, 'metadata_url': 'https://data360files.worldbank.org/data360-data/metadata/UNDRR_SFM/UNDRR_SFM_A1.pdf', 'country': country, 'unit': 'deaths and missing per 100,000 persons', 'scope': '归因于灾害的死亡及失踪人数之和，每 10 万人口年度比例；数据由各国仙台框架联络点报告，跨国比较受报告完整性与方法限制；不含所有受灾人员。空结果不表示零。', 'count': len(selected), 'data': selected}
if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('country')
    p.add_argument('start', type=int)
    p.add_argument('end', type=int)
    a = p.parse_args()
    print(json.dumps(disaster_mortality(a.country, a.start, a.end), ensure_ascii=False, indent=2))
