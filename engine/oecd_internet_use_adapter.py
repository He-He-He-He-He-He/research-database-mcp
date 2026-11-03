"""OECD 16–74 岁个人最近三个月上网比例。"""
import release_runtime
import csv, io, re
import requests
BASE = 'https://sdmx.oecd.org/public/rest/data/OECD.STI.DEP,DSD_ICT_HH_IND@DF_IND,1.1/'

def internet_use(area, start='2012', end=None):
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
    r = requests.get(BASE + f'{area}.A.C5B_I.PT_POP..Y16T74._T._T._T._T', params=p, timeout=30)
    if r.status_code == 204 or (r.status_code == 404 and r.text.strip() == 'NoRecordsFound'):
        rows = []
    else:
        r.raise_for_status()
        reader = csv.DictReader(io.StringIO(r.text))
        required = {'REF_AREA', 'FREQ', 'MEASURE', 'UNIT_MEASURE', 'AGE', 'SEX', 'TIME_PERIOD', 'OBS_VALUE', 'OBS_STATUS'}
        if not reader.fieldnames or not required.issubset(reader.fieldnames):
            raise RuntimeError('OECD CSV 列结构异常')
        rows = list(reader)
        if any((x['REF_AREA'] != area or x['FREQ'] != 'A' or x['MEASURE'] != 'C5B_I' or (x['UNIT_MEASURE'] != 'PT_POP') or (x['AGE'] != 'Y16T74') or (x['SEX'] != '_T') for x in rows)):
            raise RuntimeError('OECD 数据口径不符')
        rows.sort(key=lambda x: x['TIME_PERIOD'], reverse=True)
    return {'source': 'OECD ICT Access and Usage by Individuals 官方 SDMX', 'source_url': r.url, 'area': area, 'start': start, 'end': end, 'scope': '16–74 岁人群中最近三个月使用互联网的比例，百分数；非全体人口、家庭接入率或日均使用率。保留原始定义差异等状态。', 'items': rows, 'documentation': 'https://data-explorer.oecd.org/vis?df[ag]=OECD.STI.DEP&df[id]=DSD_ICT_HH_IND%40DF_IND&df[vs]=1.1'}
