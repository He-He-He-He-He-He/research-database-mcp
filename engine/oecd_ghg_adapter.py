"""OECD 温室气体排放清单，排除土地使用、土地利用变化和林业。"""
import release_runtime
import csv, io, re
import requests
BASE = 'https://sdmx.oecd.org/public/rest/data/OECD.ENV.EPI,DSD_AIR_GHG@DF_AIR_GHG,1.0/'

def ghg_emissions(area, start='2000', end=None):
    if not isinstance(area, str) or not re.fullmatch('[A-Z0-9_]{2,15}', area):
        raise ValueError('area 应为 OECD 地区代码')
    for v in (start, end):
        if v is not None and (not isinstance(v, str) or not re.fullmatch('\\d{4}', v)):
            raise ValueError('年份须为四位数字字符串')
    if start and end and (start > end):
        raise ValueError('开始年份不能晚于结束年份')
    p = {'format': 'csvfile'}
    if start:
        p['startPeriod'] = start
    if end:
        p['endPeriod'] = end
    r = requests.get(BASE + f'{area}.A.GHG._T.T_CO2E', params=p, timeout=30)
    if r.status_code == 204:
        rows = []
    else:
        r.raise_for_status()
        reader = csv.DictReader(io.StringIO(r.text))
        required = {'REF_AREA', 'FREQ', 'POLLUTANT', 'MEASURE', 'UNIT_MEASURE', 'UNIT_MULT', 'TIME_PERIOD', 'OBS_VALUE'}
        if not reader.fieldnames or not required.issubset(reader.fieldnames):
            raise RuntimeError('OECD CSV 列结构异常')
        rows = list(reader)
        if any((x['REF_AREA'] != area or x['FREQ'] != 'A' or x['POLLUTANT'] != 'GHG' or (x['MEASURE'] != '_T') or (x['UNIT_MEASURE'] != 'T_CO2E') for x in rows)):
            raise RuntimeError('OECD 统计口径不符')
        rows.sort(key=lambda x: x['TIME_PERIOD'], reverse=True)
    return {'source': 'OECD 温室气体清单官方 SDMX 数据', 'source_url': r.url, 'area': area, 'start': start, 'end': end, 'scope': '年度温室气体总排放，不含土地利用、土地利用变化和林业（LULUCF）；单位为吨二氧化碳当量，需按每条 UNIT_MULT 倍数解读（3 表示千吨）。不是仅 CO2 排放或碳足迹。', 'items': rows, 'documentation': 'https://data-explorer.oecd.org/vis?df[ag]=OECD.ENV.EPI&df[id]=DSD_AIR_GHG%40DF_AIR_GHG&df[vs]=1.0'}
