"""世界银行 WGI 六项治理维度与不确定性，经 Data360 查询。"""
import release_runtime
import argparse, json, re, subprocess
from urllib.parse import urlencode
BASE = 'https://data360api.worldbank.org/data360/data'
DIMENSIONS = {'effectiveness': 'GOV_WGI_GE', 'voice': 'GOV_WGI_VA', 'stability': 'GOV_WGI_PV', 'regulatory': 'GOV_WGI_RQ', 'law': 'GOV_WGI_RL', 'corruption': 'GOV_WGI_CC'}

def governance(country, year, dimension='effectiveness'):
    if not isinstance(country, str) or not re.fullmatch('[A-Z]{3}', country):
        raise ValueError('country 须为大写 ISO3 代码')
    if isinstance(year, bool) or not isinstance(year, int) or (not 1996 <= year <= 2100):
        raise ValueError('年份无效')
    if dimension not in DIMENSIONS:
        raise ValueError('无效治理维度')
    dims = {'DATABASE_ID': 'WB_WGI', 'INDICATOR': DIMENSIONS[dimension], 'REF_AREA': country, 'SEX': '_Z', 'AGE': '_Z', 'URBANISATION': '_Z', 'COMP_BREAKDOWN_2': '_Z', 'COMP_BREAKDOWN_3': '_Z'}
    url = BASE + '?' + urlencode({**dims, 'timePeriodFrom': year, 'timePeriodTo': year})
    p = release_runtime.run(['curl', '--fail', '--silent', '--show-error', '--max-time', '25', url], capture_output=True, text=True, timeout=30)
    if p.returncode:
        raise RuntimeError('Data360 请求失败')
    d = json.loads(p.stdout)
    rows = d.get('value')
    codes = {'WGI_EST', 'WGI_SE', 'WGI_SC', 'WGI_SC_LB', 'WGI_SC_UB', 'WGI_SR'}
    if not isinstance(d.get('count'), int) or not isinstance(rows, list) or d['count'] != len(rows):
        raise RuntimeError('Data360 数据数量异常')
    if len({r.get('COMP_BREAKDOWN_1') for r in rows}) != len(rows) or any((any((r.get(k) != v for k, v in dims.items())) or r.get('TIME_PERIOD') != str(year) or r.get('COMP_BREAKDOWN_1') not in codes or (r.get('UNIT_MULT') != 0) for r in rows)):
        raise RuntimeError('Data360 维度不匹配')
    values = {r['COMP_BREAKDOWN_1']: r['OBS_VALUE'] for r in rows}
    return {'source': 'World Bank Worldwide Governance Indicators via Data360', 'source_url': url, 'methodology': 'https://www.worldbank.org/en/publication/worldwide-governance-indicators/documentation', 'country': country, 'year': year, 'dimension': dimension, 'scope': 'WGI 基于调查和专家感知数据构建的治理估计，非直接客观测量。估计值一般约 -2.5 至 2.5，另有 0–100 治理分数及 90% 区间；不是百分位排名。比较时考虑标准误和不确定性。2025 方法修订，历史值可修订。', 'metrics': {'estimate': values.get('WGI_EST'), 'standard_error': values.get('WGI_SE'), 'score_0_100': values.get('WGI_SC'), 'score_lower_90pct': values.get('WGI_SC_LB'), 'score_upper_90pct': values.get('WGI_SC_UB'), 'source_count': values.get('WGI_SR')}, 'raw': rows}
if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('country')
    p.add_argument('year', type=int)
    p.add_argument('--dimension', choices=DIMENSIONS, default='effectiveness')
    a = p.parse_args()
    print(json.dumps(governance(a.country, a.year, a.dimension), ensure_ascii=False, indent=2))
