"""国家统计局 2026 年全国与分地区夏粮统计原表。"""
import release_runtime
import argparse, json, re, requests
from bs4 import BeautifulSoup
URL = 'https://www.stats.gov.cn/sj/zxfbhjd/202607/t20260710_1964090.html'

def summer_grain(region=None, timeout=15):
    if region is not None and (not isinstance(region, str) or len(region) > 20):
        raise ValueError('地区无效')
    r = requests.get(URL, timeout=timeout)
    r.raise_for_status()
    s = BeautifulSoup(r.content, 'html.parser')
    tables = s.find_all('table')
    if not tables:
        raise ValueError('未找到官方原表')
    raw = [[c.get_text(' ', strip=True) for c in tr.find_all(['td', 'th'], recursive=False)] for tr in tables[0].find_all('tr')]
    if len(raw) != 35 or raw[1][0] != '全国总计':
        raise ValueError('原表结构已变化')
    rows = [{'region': re.sub('\\s+', '', x[0]), 'values': x[1:]} for x in raw[1:] if len(x) == 4 and x[0].strip()]
    if region is not None:
        rows = [x for x in rows if x['region'] == region]
    notes = [x[0] for x in raw if len(x) == 1 and x[0].startswith('注：')]
    if not notes:
        raise ValueError('未找到原表注释')
    return {'source': '国家统计局 2026 年夏粮产量公告', 'source_url': URL, 'year': 2026, 'headers': raw[0], 'rows': rows, 'notes': notes, 'note': '季别为夏粮，非全年粮食；部分地区为重点调查，甘肃、宁夏和新疆为预产数，详见原注释。'}
if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--region')
    a = p.parse_args()
    print(json.dumps(summer_grain(a.region), ensure_ascii=False, indent=2))
