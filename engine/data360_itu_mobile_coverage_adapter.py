"""ITU 4G/LTE 或 5G 移动信号人口覆盖比例。"""
import release_runtime
import argparse, json, re, subprocess
from urllib.parse import urlencode
BASE = 'https://data360api.worldbank.org/data360/data'
CODES = {'4g': 'MOB_COV_4G', '5g': 'MOB_COV_5G'}

def mobile_coverage(country, year, generation='4g'):
    if not isinstance(country, str) or not re.fullmatch('[A-Z]{3}', country):
        raise ValueError('country 须为大写 ISO3 代码')
    if isinstance(year, bool) or not isinstance(year, int) or (not 2000 <= year <= 2100):
        raise ValueError('年份无效')
    if generation not in CODES:
        raise ValueError('generation 须为 4g 或 5g')
    dims = {'DATABASE_ID': 'ITU_DH', 'INDICATOR': CODES[generation], 'REF_AREA': country, 'SEX': '_Z', 'AGE': '_Z', 'URBANISATION': '_Z', 'COMP_BREAKDOWN_1': '_Z', 'COMP_BREAKDOWN_2': '_Z', 'COMP_BREAKDOWN_3': '_Z'}
    url = BASE + '?' + urlencode({**dims, 'timePeriodFrom': year, 'timePeriodTo': year})
    p = release_runtime.run(['curl', '--fail', '--silent', '--show-error', '--max-time', '25', url], capture_output=True, text=True, timeout=30)
    if p.returncode:
        raise RuntimeError('Data360 请求失败')
    d = json.loads(p.stdout)
    rows = d.get('value')
    if not isinstance(d.get('count'), int) or not isinstance(rows, list) or d['count'] != len(rows) or (len(rows) > 1):
        raise RuntimeError('Data360 数据数量异常')
    if any((any((r.get(k) != v for k, v in dims.items())) or r.get('TIME_PERIOD') != str(year) or r.get('UNIT_MEASURE') != 'PT_POP' or (r.get('UNIT_MULT') != 0) or (r.get('FREQ') != 'A') for r in rows)):
        raise RuntimeError('Data360 维度或单位不匹配')
    return {'source': 'ITU DataHub via World Bank Data360', 'source_url': url, 'metadata_url': 'https://data360files.worldbank.org/data360-data/metadata/ITU_DH/' + CODES[generation] + '.pdf', 'country': country, 'year': year, 'generation': generation, 'unit': 'percent of population', 'scope': '居住在至少指定制式移动信号范围内的人口比例，不要求订阅或实际使用；不是国土覆盖率，也不是网络下载速度。空结果不是零。', 'data': rows}
if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('country')
    p.add_argument('year', type=int)
    p.add_argument('--generation', choices=CODES, default='4g')
    a = p.parse_args()
    print(json.dumps(mobile_coverage(a.country, a.year, a.generation), ensure_ascii=False, indent=2))
