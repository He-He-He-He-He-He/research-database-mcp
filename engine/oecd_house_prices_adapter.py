"""OECD 官方实际住宅价格指数，季度序列。"""
import release_runtime
import csv, io, re
import requests
BASE = 'https://sdmx.oecd.org/public/rest/data/OECD.ECO.MPD,DSD_AN_HOUSE_PRICES@DF_HOUSE_PRICES,1.0/'

def real_house_price(area, start='2020-Q1', end=None):
    if not isinstance(area, str) or not re.fullmatch('[A-Z0-9_]{2,15}', area):
        raise ValueError('area 须为 OECD 地区代码，如 USA、DEU')
    for value in [start, end]:
        if value is not None and (not isinstance(value, str) or not re.fullmatch('\\d{4}-Q[1-4]', value)):
            raise ValueError('季度须为 YYYY-Q1 至 YYYY-Q4')
    if start and end and (start > end):
        raise ValueError('开始季度不能晚于结束季度')
    p = {'format': 'csvfile'}
    if start:
        p['startPeriod'] = start
    if end:
        p['endPeriod'] = end
    r = requests.get(BASE + f'{area}.Q.RHP.IX', params=p, timeout=30)
    if r.status_code == 204:
        rows = []
    else:
        r.raise_for_status()
        reader = csv.DictReader(io.StringIO(r.text))
        required = {'REF_AREA', 'FREQ', 'MEASURE', 'UNIT_MEASURE', 'TIME_PERIOD', 'OBS_VALUE', 'ADJUSTMENT', 'BASE_PER'}
        if not reader.fieldnames or not required.issubset(reader.fieldnames):
            raise RuntimeError('OECD CSV 列结构异常')
        rows = list(reader)
        if any((x['REF_AREA'] != area or x['FREQ'] != 'Q' or x['MEASURE'] != 'RHP' or (x['UNIT_MEASURE'] != 'IX') for x in rows)):
            raise RuntimeError('OECD 统计口径不符')
        rows.sort(key=lambda x: x['TIME_PERIOD'], reverse=True)
    return {'source': 'OECD Analytical house prices indicators 官方 SDMX API', 'source_url': r.url, 'area': area, 'start': start, 'end': end, 'scope': '季度实际住宅价格指数，不是房价金额或涨幅；各记录的基期和调整方式以 BASE_PER、ADJUSTMENT 为准。', 'items': rows, 'documentation': 'https://www.oecd.org/en/data/indicators/housing-prices.html'}
