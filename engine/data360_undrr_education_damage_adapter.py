"""联合国仙台框架多国灾害损毁教育设施数量。"""
import release_runtime
import argparse, json, re, subprocess
from urllib.parse import urlencode
BASE = 'https://data360api.worldbank.org/data360/data'

def damaged_education_facilities(country, start, end):
    if not isinstance(country, str) or not re.fullmatch('[A-Z]{3}', country):
        raise ValueError('country 须为大写 ISO3 代码')
    if any((isinstance(x, bool) or not isinstance(x, int) for x in (start, end))) or not 1900 <= start <= end <= 2100:
        raise ValueError('年份范围无效')
    dims = {'DATABASE_ID': 'UNDRR_SFM', 'INDICATOR': 'UNDRR_SFM_D3', 'REF_AREA': country, 'SEX': '_Z', 'AGE': '_Z', 'URBANISATION': '_Z', 'COMP_BREAKDOWN_1': '_T', 'COMP_BREAKDOWN_2': '_Z', 'COMP_BREAKDOWN_3': '_Z', 'FREQ': 'A'}
    url = BASE + '?' + urlencode({**dims, 'timePeriodFrom': start, 'timePeriodTo': end})
    p = release_runtime.run(['curl', '--fail', '--silent', '--show-error', '--max-time', '25', url], capture_output=True, text=True, timeout=30)
    if p.returncode:
        raise RuntimeError('Data360 请求失败')
    d = json.loads(p.stdout)
    rows = d.get('value')
    if not isinstance(d.get('count'), int) or not isinstance(rows, list) or d['count'] != len(rows):
        raise RuntimeError('Data360 数据数量异常')
    if any((any((r.get(k) != v for k, v in dims.items())) or r.get('UNIT_MEASURE') != 'FAC' or r.get('UNIT_MULT') != 0 for r in rows)):
        raise RuntimeError('Data360 维度或单位不匹配')
    selected = [r for r in rows if r['UNIT_MEASURE'] == 'FAC']
    return {'source': 'UNDRR Sendai Framework Monitor via World Bank Data360', 'source_url': url, 'metadata_url': 'https://data360files.worldbank.org/data360-data/metadata/UNDRR_SFM/UNDRR_SFM_D3.pdf', 'country': country, 'unit': 'facilities', 'scope': '因灾害损坏或毁坏的教育设施数量，年度上报总计，不是师生人数；跨国比较受报告完整性和方法限制；空结果不表示零。', 'count': len(selected), 'data': selected}
if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('country')
    p.add_argument('start', type=int)
    p.add_argument('end', type=int)
    a = p.parse_args()
    print(json.dumps(damaged_education_facilities(a.country, a.start, a.end), ensure_ascii=False, indent=2))
