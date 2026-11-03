"""国家统计局 2023–2024 年粮食和棉花全国及分省统计公告原表。"""
import release_runtime
import argparse
import json
import re
import requests
from bs4 import BeautifulSoup
SOURCES = {(2023, 'grain'): ('https://www.stats.gov.cn/sj/zxfb/202312/t20231211_1945417.html', 1), (2024, 'grain'): ('https://www.stats.gov.cn/sj/zxfb/202412/t20241213_1957744.html', 1), (2024, 'cotton'): ('https://www.stats.gov.cn/sj/zxfb/202412/t20241225_1957879.html', 0)}

def crop_history(crop='grain', year=2024, region=None, timeout=15):
    if (year, crop) not in SOURCES:
        raise ValueError('支持 2023 和 2024 粮食，以及 2024 棉花')
    if region is not None and (not isinstance(region, str) or len(region) > 20):
        raise ValueError('地区参数无效')
    url, index = SOURCES[year, crop]
    r = requests.get(url, timeout=timeout)
    r.raise_for_status()
    soup = BeautifulSoup(r.content, 'html.parser')
    tables = soup.find_all('table')
    if len(tables) <= index:
        raise ValueError('官方表格结构已变化')
    rows = [[c.get_text(' ', strip=True) for c in tr.find_all(['td', 'th'], recursive=False)] for tr in tables[index].find_all('tr')]
    if len(rows) < 32 or not any(('全国总计' in ' '.join(row) for row in rows)):
        raise ValueError('未找到全国及分省原表')
    first = 1
    notes = [row[0] for row in rows[first:] if len(row) == 1 and row[0] not in ('注：', '')]
    data = []
    for row in rows[first:]:
        if len(row) != 4:
            continue
        name = re.sub('\\s+', '', row[0])
        if not name:
            continue
        data.append({'region': name, 'values': row[1:]})
    if region is not None:
        data = [x for x in data if x['region'] == region]
    headers = rows[0]
    return {'source': '国家统计局', 'source_url': url, 'year': year, 'crop': crop, 'headers': headers, 'rows': data, 'notes': notes, 'note': '保留官方原值和空白；棉花空白的含义须结合原表注释，不一律视为零。'}
if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('crop', choices=['grain', 'cotton'])
    p.add_argument('year', type=int)
    p.add_argument('--region')
    a = p.parse_args()
    print(json.dumps(crop_history(a.crop, a.year, a.region), ensure_ascii=False, indent=2))
