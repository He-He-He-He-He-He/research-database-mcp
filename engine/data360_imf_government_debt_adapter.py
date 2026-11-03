"""IMF WEO 一般政府债务总额占 GDP 比例，经 Data360 提供。"""
import release_runtime
import argparse, json, re, subprocess
from urllib.parse import urlencode
BASE = 'https://data360api.worldbank.org/data360/data'

def government_debt(country, start, end):
    if not isinstance(country, str) or not re.fullmatch('[A-Z]{3}', country):
        raise ValueError('country 须为大写 ISO3 代码')
    if any((isinstance(x, bool) or not isinstance(x, int) for x in (start, end))) or not 1900 <= start <= end <= 2100:
        raise ValueError('年份范围无效')
    dims = {'DATABASE_ID': 'IMF_WEO', 'INDICATOR': 'IMF_WEO_GGXWDG_NGDP', 'REF_AREA': country, 'SEX': '_Z', 'AGE': '_Z', 'URBANISATION': '_Z', 'COMP_BREAKDOWN_1': 'V_LST', 'COMP_BREAKDOWN_2': '_Z', 'COMP_BREAKDOWN_3': '_Z'}
    url = BASE + '?' + urlencode({**dims, 'timePeriodFrom': start, 'timePeriodTo': end})
    p = release_runtime.run(['curl', '--fail', '--silent', '--show-error', '--max-time', '25', url], capture_output=True, text=True, timeout=30)
    if p.returncode:
        raise RuntimeError('Data360 请求失败')
    d = json.loads(p.stdout)
    rows = d.get('value')
    if not isinstance(d.get('count'), int) or not isinstance(rows, list) or d['count'] != len(rows):
        raise RuntimeError('Data360 数据数量异常')
    if any((any((r.get(k) != v for k, v in dims.items())) or r.get('UNIT_MEASURE') != 'PT_GDP' or r.get('UNIT_MULT') != 0 or (r.get('FREQ') != 'A') for r in rows)):
        raise RuntimeError('Data360 维度或单位不匹配')
    return {'source': 'IMF World Economic Outlook via World Bank Data360', 'source_url': url, 'documentation': 'https://data.imf.org/en/datasets/IMF.RES:WEO', 'country': country, 'indicator': 'General government gross debt', 'unit': 'percent of GDP', 'scope': '一般政府债务总额相对 GDP 的比例，非仅中央政府债务，也不是年度赤字。WEO 包含预测、估计和历史数据；此 Data360 返回的 OBS_STATUS 不足以可靠区分预测与实绩，年份可能按财年或日历年标注，应查 IMF 对应版本各国元数据；例如埃及财年以6月30日结束，需核对具体数据如何归年。历史数值也可能修订。', 'count': len(rows), 'data': rows}
if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('country')
    p.add_argument('start', type=int)
    p.add_argument('end', type=int)
    a = p.parse_args()
    print(json.dumps(government_debt(a.country, a.start, a.end), ensure_ascii=False, indent=2))
