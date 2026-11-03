"""WIPO 各经济体 ICT 专利公开量。"""
import release_runtime
import argparse, json, re, subprocess
from urllib.parse import urlencode
BASE = 'https://data360api.worldbank.org/data360/data'

def ict_patent_publications(country, start, end):
    if not isinstance(country, str) or not re.fullmatch('[A-Z]{3}', country):
        raise ValueError('country 须为大写 ISO3 代码')
    if any((isinstance(x, bool) or not isinstance(x, int) for x in (start, end))) or not 1900 <= start <= end <= 2100:
        raise ValueError('年份范围无效')
    dims = {'DATABASE_ID': 'WIPO_ICT', 'INDICATOR': 'WIPO_ICT_PAT_PUB_TOT', 'REF_AREA': country, 'SEX': '_T', 'AGE': '_T', 'URBANISATION': '_T', 'COMP_BREAKDOWN_1': '_Z', 'COMP_BREAKDOWN_2': '_Z', 'COMP_BREAKDOWN_3': '_Z'}
    url = BASE + '?' + urlencode({**dims, 'timePeriodFrom': start, 'timePeriodTo': end})
    p = release_runtime.run(['curl', '--fail', '--silent', '--show-error', '--max-time', '25', url], capture_output=True, text=True, timeout=30)
    if p.returncode:
        raise RuntimeError('Data360 请求失败')
    d = json.loads(p.stdout)
    rows = d.get('value')
    if not isinstance(d.get('count'), int) or not isinstance(rows, list) or d['count'] != len(rows):
        raise RuntimeError('Data360 数据数量异常')
    if any((any((r.get(k) != v for k, v in dims.items())) or r.get('UNIT_MEASURE') != 'PATN' or r.get('UNIT_MULT') != 0 or (r.get('FREQ') != 'A') for r in rows)):
        raise RuntimeError('Data360 维度或单位不匹配')
    return {'source': 'WIPO Intellectual Property Statistics via World Bank Data360', 'source_url': url, 'metadata_url': 'https://data360files.worldbank.org/data360-data/metadata/WIPO_ICT/WIPO_ICT_PAT_PUB_TOT.pdf', 'country': country, 'indicator': 'Number of ICT patent publications: all categories', 'unit': 'patent publications', 'scope': '按申请人来源地统计数字领域公开专利数量，不等于授权数或 PCT 国际申请数；可能随源数据修订。返回原始状态及单位乘数，具体技术分类见官方元数据。', 'count': len(rows), 'data': rows}
if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('country')
    p.add_argument('start', type=int)
    p.add_argument('end', type=int)
    a = p.parse_args()
    print(json.dumps(ict_patent_publications(a.country, a.start, a.end), ensure_ascii=False, indent=2))
