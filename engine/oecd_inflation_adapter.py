"""OECD 月度 CPI 同比变化：国家 CPI、总项、未季调。"""
import release_runtime
import csv, io, re
import requests
BASE = 'https://sdmx.oecd.org/public/rest/data/OECD.SDD.TPS,DSD_PRICES@DF_PRICES_ALL,1.0/'

def cpi_inflation(area, start='2020-01', end=None):
    if not isinstance(area, str) or not re.fullmatch('[A-Z0-9_]{2,15}', area):
        raise ValueError('area 须为 OECD 地区代码，例如 USA、CHN 或 DEU')
    for value in [start, end]:
        if value is not None and (not isinstance(value, str) or not re.fullmatch('\\d{4}-(?:0[1-9]|1[0-2])', value)):
            raise ValueError('月份须为 YYYY-MM')
    if start and end and (start > end):
        raise ValueError('开始月份不能晚于结束月份')
    p = {'format': 'csvfile'}
    if start:
        p['startPeriod'] = start
    if end:
        p['endPeriod'] = end
    r = requests.get(BASE + f'{area}.M.N.CPI.PA._T.N.GY', params=p, timeout=30)
    if r.status_code == 204:
        rows = []
    else:
        r.raise_for_status()
        reader = csv.DictReader(io.StringIO(r.text))
        required = {'TIME_PERIOD', 'OBS_VALUE', 'REF_AREA', 'ADJUSTMENT', 'UNIT_MEASURE', 'TRANSFORMATION', 'METHODOLOGY', 'MEASURE'}
        if not reader.fieldnames or not required.issubset(reader.fieldnames):
            raise RuntimeError('OECD CSV 列结构异常')
        rows = list(reader)
        if any((x['REF_AREA'] != area or x['ADJUSTMENT'] != 'N' or x['UNIT_MEASURE'] != 'PA' or (x['TRANSFORMATION'] != 'GY') or (x['METHODOLOGY'] != 'N') or (x['MEASURE'] != 'CPI') for x in rows)):
            raise RuntimeError('OECD 返回的统计口径不符')
        rows.sort(key=lambda x: x['TIME_PERIOD'], reverse=True)
    return {'source': 'OECD 官方 SDMX 价格统计', 'source_url': r.url, 'area': area, 'start': start, 'end': end, 'scope': '月度全国 CPI 全部项目，对上年同月变化率，百分数，未作季节或日历调整；不是物价指数本身。', 'items': rows, 'documentation': 'https://data-explorer.oecd.org/vis?df[ag]=OECD.SDD.TPS&df[id]=DSD_PRICES%40DF_PRICES_ALL&df[vs]=1.0'}
