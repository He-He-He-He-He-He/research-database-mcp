"""临夏州统计月报载各县（市）年末常住人口。"""
import release_runtime
import re, requests
from bs4 import BeautifulSoup
URLS = {2022: 'https://linxia.gov.cn/lxz/zwgk/fdzdgknr/tjsj/tjyb/art/2023/art_75b901630e4c416dbb243cf2e949d833.html', 2023: 'https://linxia.gov.cn/lxz/zwgk/fdzdgknr/tjsj/tjyb/art/2024/art_27ca195d23d74f1e99d8b61ff7fafec1.html', 2024: 'https://linxia.gov.cn/lxz/zwgk/fdzdgknr/tjsj/tjyb/art/2025/art_4f5e5ebad9bc4e22b26711c265189166.html', 2025: 'https://www.linxia.gov.cn/lxz/zwgk/fdzdgknr/tjsj/tjyb/art/2026/art_c6a9a2ce3cfc443cbd703a4ad4ad1d92.html'}
REGIONS = '临夏市 临夏县 康乐县 永靖县 广河县 和政县 东乡县 积石山县'.split()

def data(year, region=None):
    if isinstance(year, bool) or year not in URLS:
        raise ValueError('仅支持2022–2025人口数据年份')
    if region is not None and region not in REGIONS:
        raise ValueError('地区不存在')
    r = requests.get(URLS[year], timeout=35)
    r.raise_for_status()
    s = BeautifulSoup(r.content, 'html.parser')
    match = []
    for table in s.find_all('table'):
        text = ''.join(table.get_text(' ', strip=True).split())
        if all((k in text for k in ('临夏市', '临夏县', '常住人口', '城镇化率'))):
            match.append(table)
    if len(match) != 1:
        raise ValueError('人口表未唯一定位')
    t = match[0]
    headers = ''.join(t.find('tr').get_text(' ', strip=True).split())
    if year == 2025 and '城镇人口' not in headers:
        raise ValueError('2025城镇人口表头异常')
    if year != 2025 and '自增率' not in headers:
        raise ValueError('自然增长率表头异常')
    rows = []
    for tr in t.find_all('tr'):
        c = [''.join(x.get_text(' ', strip=True).split()) for x in tr.find_all(['td', 'th'], recursive=False)]
        if len(c) != 4 or c[0] not in REGIONS:
            continue
        if not all((re.fullmatch('-?\\d+(?:\\.\\d+)?', v) for v in c[1:])):
            raise ValueError('数字列异常')
        a, b, d = map(float, c[1:])
        row = {'地区': c[0], '常住人口_万人': a}
        if year == 2025:
            row.update({'城镇人口_万人': b, '城镇化率_百分比': d})
        else:
            row.update({'城镇化率_百分比': b, '人口自然增长率_千分比': d})
        rows.append(row)
    if [x['地区'] for x in rows] != REGIONS:
        raise ValueError('地区数量或顺序异常')
    if region:
        rows = [x for x in rows if x['地区'] == region]
    return {'source': '临夏州统计局主要指标完成情况表', 'year': year, 'url': URLS[year], 'note': '年末常住人口：2022–2024表列自然增长率，2025表列城镇人口；报告月份是网页发布时间区间，不是人口数据年份。调查与行政区划及修订口径以原表为准。', 'rows': rows}
