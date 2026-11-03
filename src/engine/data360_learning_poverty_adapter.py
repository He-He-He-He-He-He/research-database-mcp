"""世界银行/UNESCO 儿童学习贫困率，经 Data360 WDI 查询。"""
import release_runtime
import argparse, json, re, subprocess
from urllib.parse import urlencode
BASE = 'https://data360api.worldbank.org/data360/data'

def learning_poverty(country, start, end):
    if not isinstance(country, str) or not re.fullmatch('[A-Z]{3}', country):
        raise ValueError('country 须为大写 ISO3 代码')
    if any((isinstance(x, bool) or not isinstance(x, int) for x in (start, end))) or not 1900 <= start <= end <= 2100:
        raise ValueError('年份范围无效')
    dims = {'DATABASE_ID': 'WB_WDI', 'INDICATOR': 'WB_WDI_SE_LPV_PRIM', 'REF_AREA': country, 'SEX': '_T', 'AGE': '_T', 'URBANISATION': '_T', 'COMP_BREAKDOWN_1': '_Z', 'COMP_BREAKDOWN_2': '_Z', 'COMP_BREAKDOWN_3': '_Z'}
    url = BASE + '?' + urlencode({'DATABASE_ID': dims['DATABASE_ID'], 'INDICATOR': dims['INDICATOR'], 'REF_AREA': country, 'timePeriodFrom': start, 'timePeriodTo': end})
    p = release_runtime.run(['curl', '--fail', '--silent', '--show-error', '--max-time', '25', url], capture_output=True, text=True, timeout=30)
    if p.returncode:
        raise RuntimeError('Data360 请求失败')
    d = json.loads(p.stdout)
    rows = d.get('value')
    if not isinstance(d.get('count'), int) or not isinstance(rows, list) or d['count'] != len(rows):
        raise RuntimeError('Data360 数据数量异常')
    if any((any((r.get(k) != v for k, v in dims.items())) or r.get('UNIT_MEASURE') != 'PT' or r.get('UNIT_MULT') != 0 or (r.get('FREQ') != 'A') for r in rows)):
        raise RuntimeError('Data360 维度或单位不匹配')
    return {'source': 'World Bank and UNESCO Institute for Statistics via World Bank Data360 WDI', 'source_url': url, 'methodology': 'https://www.worldbank.org/en/brief/2021/07/01/learning-poverty-measure', 'country': country, 'unit': 'percent', 'scope': '小学结束年龄儿童低于基本阅读熟练度的估计比例，并按失学儿童比例调整；失学儿童假设未达到熟练度。非普通成人识字率、不是逐一测得所有儿童。调查与测评年份可能不同于报告参考年；数据可修订，空结果不表示零。', 'count': len(rows), 'data': rows}
if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('country')
    p.add_argument('start', type=int)
    p.add_argument('end', type=int)
    a = p.parse_args()
    print(json.dumps(learning_poverty(a.country, a.start, a.end), ensure_ascii=False, indent=2))
