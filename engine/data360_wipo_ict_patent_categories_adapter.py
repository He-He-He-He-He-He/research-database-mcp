"""WIPO ICT 专利公开量按数字技术领域分类。"""
import release_runtime
import argparse, json, re, subprocess
from urllib.parse import urlencode
BASE = 'https://data360api.worldbank.org/data360/data'
CODES = {'WIPO_ICT_PAT_PUB_TOT': 'all_ict', 'WIPO_ICT_PAT_PUB_COMPTEC': 'computer_technology', 'WIPO_ICT_PAT_PUB_AUDIO': 'audiovisual_technology', 'WIPO_ICT_PAT_PUB_IT_MTHD': 'it_methods_for_management', 'WIPO_ICT_PAT_PUB_DIGCOM': 'digital_communication', 'WIPO_ICT_PAT_PUB_TELE': 'telecommunications'}

def patent_categories(country, year):
    if not isinstance(country, str) or not re.fullmatch('[A-Z]{3}', country):
        raise ValueError('country 须为大写 ISO3 代码')
    if isinstance(year, bool) or not isinstance(year, int) or (not 1900 <= year <= 2100):
        raise ValueError('年份无效')
    dims = {'DATABASE_ID': 'WIPO_ICT', 'REF_AREA': country, 'SEX': '_T', 'AGE': '_T', 'URBANISATION': '_T', 'COMP_BREAKDOWN_1': '_Z', 'COMP_BREAKDOWN_2': '_Z', 'COMP_BREAKDOWN_3': '_Z'}
    url = BASE + '?' + urlencode({**dims, 'timePeriodFrom': year, 'timePeriodTo': year})
    p = release_runtime.run(['curl', '--fail', '--silent', '--show-error', '--max-time', '25', url], capture_output=True, text=True, timeout=30)
    if p.returncode:
        raise RuntimeError('Data360 请求失败')
    d = json.loads(p.stdout)
    rows = d.get('value')
    if not isinstance(d.get('count'), int) or not isinstance(rows, list) or d['count'] != len(rows):
        raise RuntimeError('Data360 数据数量异常')
    selected = [r for r in rows if r.get('INDICATOR') in CODES]
    if len({r['INDICATOR'] for r in selected}) != len(selected) or any((any((r.get(k) != v for k, v in dims.items())) or r.get('TIME_PERIOD') != str(year) or r.get('UNIT_MEASURE') != 'PATN' or (r.get('UNIT_MULT') != 0) or (r.get('FREQ') != 'A') for r in selected)):
        raise RuntimeError('Data360 维度或单位不匹配')
    return {'source': 'WIPO Intellectual Property Statistics via World Bank Data360', 'source_url': url, 'metadata_base': 'https://data360files.worldbank.org/data360-data/metadata/WIPO_ICT/', 'country': country, 'year': year, 'unit': 'patent publications', 'scope': '按申请人来源地统计 ICT 专利公开量，按计算机、视听、管理信息技术方法、数字通信、电信等类别列示；不是专利授权量、PCT 申请量或专利质量。保留源记录和状态，空缺不作零。', 'categories': {CODES[r['INDICATOR']]: r['OBS_VALUE'] for r in selected}, 'data': selected}
if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('country')
    p.add_argument('year', type=int)
    a = p.parse_args()
    print(json.dumps(patent_categories(a.country, a.year), ensure_ascii=False, indent=2))
