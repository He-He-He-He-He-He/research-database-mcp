"""ITU 各国低用量语音短信和移动数据价格篮，经 Data360 查询。"""
import release_runtime
import argparse, json, re, subprocess
from urllib.parse import urlencode
BASE = 'https://data360api.worldbank.org/data360/data'

def mobile_voice_data_price(country, year):
    if not isinstance(country, str) or not re.fullmatch('[A-Z]{3}', country):
        raise ValueError('country 须为大写 ISO3 代码')
    if isinstance(year, bool) or not isinstance(year, int) or (not 2018 <= year <= 2100):
        raise ValueError('年份无效')
    dims = {'DATABASE_ID': 'ITU_DH', 'INDICATOR': 'PRI_LU_VD', 'REF_AREA': country, 'SEX': '_Z', 'AGE': '_Z', 'URBANISATION': '_Z', 'COMP_BREAKDOWN_1': '_Z', 'COMP_BREAKDOWN_2': '_Z', 'COMP_BREAKDOWN_3': '_Z'}
    url = BASE + '?' + urlencode({**dims, 'timePeriodFrom': year, 'timePeriodTo': year})
    p = release_runtime.run(['curl', '--fail', '--silent', '--show-error', '--max-time', '25', url], capture_output=True, text=True, timeout=30)
    if p.returncode:
        raise RuntimeError('Data360 请求失败')
    d = json.loads(p.stdout)
    rows = d.get('value')
    units = {'USD', 'PPP', 'PT_GNI_PS'}
    if not isinstance(d.get('count'), int) or not isinstance(rows, list) or d['count'] != len(rows):
        raise RuntimeError('Data360 数据数量异常')
    if len({r.get('UNIT_MEASURE') for r in rows}) != len(rows) or any((any((r.get(k) != v for k, v in dims.items())) or r.get('TIME_PERIOD') != str(year) or r.get('UNIT_MEASURE') not in units or (r.get('UNIT_MULT') != 0) or (r.get('FREQ') != 'A') for r in rows)):
        raise RuntimeError('Data360 维度或单位不匹配')
    return {'source': 'ITU DataHub via World Bank Data360', 'source_url': url, 'metadata_url': 'https://data360files.worldbank.org/data360-data/metadata/ITU_DH/PRI_LU_VD.pdf', 'country': country, 'year': year, 'scope': '低用量语音及数据月套餐，至少含 70 分钟语音、20 条短信和 500MB 数据，网络至少 3G；选用市场份额最大的运营商住宅用户非促销价格。返回当期美元、购买力平价美元和人均月 GNI 百分比，单位不可混用。空结果不是零，历史值并非当前报价。', 'count': len(rows), 'data': rows}
if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('country')
    p.add_argument('year', type=int)
    a = p.parse_args()
    print(json.dumps(mobile_voice_data_price(a.country, a.year), ensure_ascii=False, indent=2))
