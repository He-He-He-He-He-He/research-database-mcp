"""生态环境部数据服务公开的城市 AQI 实时及日报快照。"""
import release_runtime
import re
import requests
from bs4 import BeautifulSoup
URL = 'https://datacenter.mee.gov.cn/websjzx/homepages/airDatas.vm'

def snapshot(kind='hour', city=''):
    if kind not in ('hour', 'day'):
        raise ValueError('kind 仅支持 hour 或 day')
    if not isinstance(city, str) or len(city) > 100:
        raise ValueError('城市关键词最多 100 个字符')
    r = requests.get(URL, timeout=25, allow_redirects=False)
    r.raise_for_status()
    if r.is_redirect or len(r.content) > 10000000:
        raise ValueError('响应跳转或过大')
    r.encoding = 'utf-8'
    s = BeautifulSoup(r.text, 'html.parser')
    table = s.select_one('#legend_01_table' if kind == 'hour' else '#legend_02_table')
    timestamp = s.select_one('#hour' if kind == 'hour' else '#day')
    if not table or not timestamp:
        raise ValueError('未识别原始表格或时间')
    items = []
    all_count = 0
    for row in table.select('tr'):
        cells = [c.get_text(' ', strip=True) for c in row.find_all('td', recursive=False)]
        if len(cells) != (3 if kind == 'hour' else 4):
            continue
        all_count += 1
        if city not in cells[0]:
            continue
        match = re.search("openWin[12]\\('[^']*','[^']*','(\\d{6})'\\)", row.get('onclick', ''))
        item = {'city': cells[0], 'city_code': match.group(1) if match else None, 'aqi': int(cells[1]) if cells[1].isdigit() else None, 'aqi_raw': cells[1], 'primary_pollutant': cells[-1], 'health_guidance': row.get('title', '').strip()}
        if kind == 'day':
            item['level'] = cells[2]
        items.append(item)
    if all_count < 100:
        raise ValueError('城市数量过少，上游页面可能变化或数据不完整')
    return {'source': '中华人民共和国生态环境部数据服务', 'source_url': URL, 'kind': kind, 'time_as_published': timestamp.get('value'), 'available_city_count': all_count, 'filter': city, 'matched_count': len(items), 'items': items, 'note': '仅当前网页快照，小时值与日报统计时段不同，不是历史数据库；缺失值保留原文且不视作零。请以官网最新信息和健康指引为准。'}
