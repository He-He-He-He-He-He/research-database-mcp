"""FAO AQUASTAT 各经济体大型水坝累计理论蓄水容量。"""
import release_runtime
import argparse, json, re, subprocess
from urllib.parse import urlencode
BASE = 'https://data360api.worldbank.org/data360/data'

def dam_capacity(country, start, end):
    if not isinstance(country, str) or not re.fullmatch('[A-Z]{3}', country):
        raise ValueError('country 须为大写 ISO3 代码')
    if any((isinstance(x, bool) or not isinstance(x, int) for x in (start, end))) or not 1900 <= start <= end <= 2100:
        raise ValueError('年份范围无效')
    dims = {'DATABASE_ID': 'FAO_AS', 'INDICATOR': 'FAO_AS_4197', 'REF_AREA': country, 'SEX': '_Z', 'AGE': '_Z', 'URBANISATION': '_Z', 'COMP_BREAKDOWN_1': '_Z', 'COMP_BREAKDOWN_2': '_Z', 'COMP_BREAKDOWN_3': '_Z'}
    url = BASE + '?' + urlencode({**dims, 'timePeriodFrom': start, 'timePeriodTo': end})
    p = release_runtime.run(['curl', '--fail', '--silent', '--show-error', '--max-time', '25', url], capture_output=True, text=True, timeout=30)
    if p.returncode:
        raise RuntimeError('Data360 请求失败')
    d = json.loads(p.stdout)
    rows = d.get('value')
    if not isinstance(d.get('count'), int) or not isinstance(rows, list) or d['count'] != len(rows):
        raise RuntimeError('Data360 数据数量异常')
    if any((any((r.get(k) != v for k, v in dims.items())) or r.get('UNIT_MEASURE') != 'KM3' or r.get('UNIT_MULT') != 0 or (r.get('FREQ') != 'A') for r in rows)):
        raise RuntimeError('Data360 维度或单位不匹配')
    return {'source': 'FAO AQUASTAT via World Bank Data360', 'source_url': url, 'metadata_url': 'https://data360.worldbank.org/en/indicator/FAO_AS_4197', 'country': country, 'indicator': 'Total dam capacity', 'unit': 'cubic kilometres', 'scope': '所有大型水坝初始设计蓄水容量的累计值；不是当年实际蓄水量，淤积可降低实际容量，小型水坝可能未列入。返回原始状态及单位乘数。', 'count': len(rows), 'data': rows}
if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('country')
    p.add_argument('start', type=int)
    p.add_argument('end', type=int)
    a = p.parse_args()
    print(json.dumps(dam_capacity(a.country, a.start, a.end), ensure_ascii=False, indent=2))
