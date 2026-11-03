"""UNESCO UIS Data Browser 官方教育、科学与文化指标 API。"""
import release_runtime
import argparse, json, re, subprocess
from urllib.parse import urlencode
BASE = 'https://api.uis.unesco.org/api/public/data/indicators'

def uis_series(indicator, country, start, end):
    if not isinstance(indicator, str) or not re.fullmatch('[A-Za-z0-9_.-]{1,80}', indicator):
        raise ValueError('indicator 格式无效')
    if not isinstance(country, str) or not re.fullmatch('[A-Z]{3}', country):
        raise ValueError('country 须为大写 ISO3 代码')
    if any((isinstance(x, bool) or not isinstance(x, int) for x in (start, end))) or not 1900 <= start <= end <= 2100:
        raise ValueError('年份范围无效')
    url = BASE + '?' + urlencode({'indicator': indicator, 'geoUnit': country, 'start': start, 'end': end, 'footnotes': 'true', 'indicatorMetadata': 'true'})
    p = release_runtime.run(['curl', '--fail', '--silent', '--show-error', '--max-time', '25', url], capture_output=True, text=True, timeout=30)
    if p.returncode:
        raise RuntimeError('UNESCO UIS API 请求失败')
    d = json.loads(p.stdout)
    rows = d.get('records')
    meta = d.get('indicatorMetadata')
    if not isinstance(rows, list) or not isinstance(meta, list):
        raise RuntimeError('UNESCO UIS API 响应结构异常')
    if any((r.get('indicatorId') != indicator or r.get('geoUnit') != country or (not isinstance(r.get('year'), int)) or (not start <= r['year'] <= end) for r in rows)):
        raise RuntimeError('UIS 响应指标、国家或年份不匹配')
    return {'source': 'UNESCO Institute for Statistics Data API', 'source_url': url, 'documentation': 'https://api.uis.unesco.org/api/public/documentation/', 'scope': 'UNESCO UIS 官方原始指标与国家序列，保留来源脚注、统计限定和指标元数据；各指标定义、单位、调查或估计方法各异，需阅读元数据；空记录不等于零。', 'hints': d.get('hints', []), 'indicator_metadata': meta, 'count': len(rows), 'data': rows}
if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('indicator')
    p.add_argument('country')
    p.add_argument('start', type=int)
    p.add_argument('end', type=int)
    a = p.parse_args()
    print(json.dumps(uis_series(a.indicator, a.country, a.start, a.end), ensure_ascii=False, indent=2))
