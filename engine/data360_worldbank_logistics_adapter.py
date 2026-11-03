"""世界银行传统物流绩效指数及六项分项（非 LPI 2.0）。"""
import release_runtime
import argparse, json, re, subprocess
from urllib.parse import urlencode
BASE = 'https://data360api.worldbank.org/data360/data'
COMPONENTS = {'_T': 'overall', 'WB_LPI_CTMS': 'customs', 'WB_LPI_INF': 'infrastructure', 'WB_LPI_IS': 'international_shipments', 'WB_LPI_LOG': 'logistics_quality', 'WB_LPI_TML': 'timeliness', 'WB_LPI_TRC': 'tracking'}

def logistics(country, year):
    if not isinstance(country, str) or not re.fullmatch('[A-Z]{3}', country):
        raise ValueError('country 须为大写 ISO3 代码')
    if isinstance(year, bool) or not isinstance(year, int) or (not 2007 <= year <= 2100):
        raise ValueError('年份无效')
    dims = {'DATABASE_ID': 'WB_LPI', 'INDICATOR': 'LPI_OVR', 'REF_AREA': country, 'SEX': '_Z', 'AGE': '_Z', 'URBANISATION': '_Z', 'COMP_BREAKDOWN_3': '_Z'}
    url = BASE + '?' + urlencode({**dims, 'timePeriodFrom': year, 'timePeriodTo': year})
    p = release_runtime.run(['curl', '--fail', '--silent', '--show-error', '--max-time', '25', url], capture_output=True, text=True, timeout=30)
    if p.returncode:
        raise RuntimeError('Data360 请求失败')
    d = json.loads(p.stdout)
    rows = d.get('value')
    if not isinstance(d.get('count'), int) or not isinstance(rows, list) or d['count'] != len(rows):
        raise RuntimeError('Data360 数据数量异常')
    seen = set()
    output = {}
    for r in rows:
        c = r.get('COMP_BREAKDOWN_1')
        metric = r.get('COMP_BREAKDOWN_2')
        if any((r.get(k) != v for k, v in dims.items())) or r.get('TIME_PERIOD') != str(year) or c not in COMPONENTS or (metric not in ('WB_LPI_SC', 'WB_LPI_RK')) or (r.get('UNIT_MULT') != 0) or ((c, metric) in seen):
            raise RuntimeError('Data360 维度不匹配')
        seen.add((c, metric))
        output.setdefault(COMPONENTS[c], {})['score' if metric == 'WB_LPI_SC' else 'rank'] = r.get('OBS_VALUE')
    return {'source': 'World Bank Logistics Performance Index via Data360', 'source_url': url, 'methodology': 'https://lpi.worldbank.org/sites/default/files/2023-04/Methodology_LPI_survey.pdf', 'country': country, 'year': year, 'scope': '传统 LPI 综合和六项分项，基于国际物流专业人士对市场的调查，分数约 1–5，另列名次；不等于实时物流速度或新 LPI 2.0。非每年都有调查，空数据不代表零，调查结果有抽样不确定性。', 'components': output, 'raw': rows}
if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('country')
    p.add_argument('year', type=int)
    a = p.parse_args()
    print(json.dumps(logistics(a.country, a.year), ensure_ascii=False, indent=2))
