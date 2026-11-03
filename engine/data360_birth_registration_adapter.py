"""UNICEF 五岁以下儿童出生登记调查，经世界银行 Data360 发布。"""
import release_runtime
import argparse, json, re, subprocess
from urllib.parse import urlencode
BASE = 'https://data360api.worldbank.org/data360/data'

def birth_registration(country, year, sex='_T'):
    if not isinstance(country, str) or not re.fullmatch('[A-Z]{3}', country):
        raise ValueError('country 须为大写 ISO3 代码')
    if isinstance(year, bool) or not isinstance(year, int) or (not 1900 <= year <= 2100):
        raise ValueError('年份无效')
    if sex not in ('_T', 'M', 'F'):
        raise ValueError('sex 仅支持 _T、M、F')
    dims = {'DATABASE_ID': 'WB_ID4D', 'INDICATOR': 'BIRTH_REG', 'REF_AREA': country, 'SEX': sex, 'AGE': 'Y0T4', 'URBANISATION': '_T', 'COMP_BREAKDOWN_1': '_Z', 'COMP_BREAKDOWN_2': '_Z', 'COMP_BREAKDOWN_3': '_Z'}
    params = {**dims, 'timePeriodFrom': str(year), 'timePeriodTo': str(year)}
    url = BASE + '?' + urlencode(params)
    p = release_runtime.run(['curl', '--fail', '--silent', '--show-error', '--max-time', '25', url], capture_output=True, text=True, timeout=30)
    if p.returncode:
        raise RuntimeError('Data360 请求失败')
    d = json.loads(p.stdout)
    rows = d.get('value')
    if not isinstance(d.get('count'), int) or not isinstance(rows, list) or d['count'] != len(rows) or (len(rows) > 1):
        raise RuntimeError('Data360 数据数量异常')
    if any((any((r.get(k) != v for k, v in dims.items())) or r.get('TIME_PERIOD') != str(year) or r.get('UNIT_MEASURE') != 'PT_CH_Y_LT5' or (r.get('UNIT_MULT') != 0) for r in rows)):
        raise RuntimeError('Data360 维度不匹配')
    return {'source': 'UNICEF, World Bank ID4D via Data360', 'source_url': url, 'documentation': 'https://data360.worldbank.org/en/search', 'country': country, 'year': year, 'sex': sex, 'unit': 'percent of children under 5', 'scope': '调查时出生已登记的 5 岁以下儿童比例；包含有出生证明者，以及无出生证明但母亲或照护者报告已登记者。按性别；空结果表示无可用数据，不是零。保留原始状态及注释。', 'data': rows}
if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('country')
    p.add_argument('year', type=int)
    p.add_argument('--sex', choices=['_T', 'M', 'F'], default='_T')
    a = p.parse_args()
    print(json.dumps(birth_registration(a.country, a.year, a.sex), ensure_ascii=False, indent=2))
