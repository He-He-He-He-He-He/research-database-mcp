"""OECD 官方出生时预期寿命，按性别返回年度数据。"""
import release_runtime
import csv, io, re
import requests
BASE = 'https://sdmx.oecd.org/public/rest/data/OECD.ELS.HD,DSD_HEALTH_STAT@DF_LE,1.1/'

def life_expectancy_birth(area, start='2000', end=None):
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
    r = requests.get(BASE + f'{area}.A.LFEXP..Y0........', params=p, timeout=30)
    if r.status_code == 204:
        rows = []
    else:
        r.raise_for_status()
        reader = csv.DictReader(io.StringIO(r.text))
        required = {'REF_AREA', 'FREQ', 'MEASURE', 'UNIT_MEASURE', 'AGE', 'SEX', 'TIME_PERIOD', 'OBS_VALUE'}
        if not reader.fieldnames or not required.issubset(reader.fieldnames):
            raise RuntimeError('OECD CSV 列结构异常')
        rows = list(reader)
        if any((x['REF_AREA'] != area or x['FREQ'] != 'A' or x['MEASURE'] != 'LFEXP' or (x['AGE'] != 'Y0') or (x['UNIT_MEASURE'] != 'Y') for x in rows)):
            raise RuntimeError('OECD 统计口径不符')
        rows.sort(key=lambda x: (x['TIME_PERIOD'], x['SEX']), reverse=True)
    return {'source': 'OECD Life expectancy 官方 SDMX 数据', 'source_url': r.url, 'area': area, 'start': start, 'end': end, 'scope': '按年份和性别的出生时预期寿命，单位年；不是个体寿命预测，保留原始性别及质量状态代码。', 'items': rows, 'documentation': 'https://data-explorer.oecd.org/vis?df[ag]=OECD.ELS.HD&df[id]=DSD_HEALTH_STAT%40DF_LE&df[vs]=1.1'}
