"""OECD Education at a Glance 高等教育学历比例。"""
import release_runtime
import csv, io, re
import requests
BASE = 'https://sdmx.oecd.org/public/rest/data/OECD.EDU.IMEP,DSD_EAG_LSO_EA@DF_LSO_NEAC_DISTR_EA,1.0/'

def tertiary_attainment(area, age='Y25T34', sex='_T', start='2010', end=None):
    if not isinstance(area, str) or not re.fullmatch('[A-Z0-9_]{2,15}', area):
        raise ValueError('area 应为 OECD 地区代码')
    if age not in {'Y25T34', 'Y25T64', 'Y55T64'}:
        raise ValueError('age 仅支持 Y25T34、Y25T64、Y55T64')
    if sex not in {'_T', 'F', 'M'}:
        raise ValueError('sex 仅支持 _T、F、M')
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
    r = requests.get(BASE + f'{area}.{sex}.{age}.ISCED11A_5T8..........OBS...A', params=p, timeout=30)
    if r.status_code == 204 or (r.status_code == 404 and r.text.strip() == 'NoRecordsFound'):
        rows = []
    else:
        r.raise_for_status()
        reader = csv.DictReader(io.StringIO(r.text))
        required = {'REF_AREA', 'SEX', 'AGE', 'ATTAINMENT_LEV', 'UNIT_MEASURE', 'FREQ', 'TIME_PERIOD', 'OBS_VALUE', 'OBS_STATUS'}
        if not reader.fieldnames or not required.issubset(reader.fieldnames):
            raise RuntimeError('OECD CSV 列结构异常')
        rows = list(reader)
        if any((x['REF_AREA'] != area or x['SEX'] != sex or x['AGE'] != age or (x['ATTAINMENT_LEV'] != 'ISCED11A_5T8') or (x['UNIT_MEASURE'] != 'PT_POP_SEX_AGE') or (x['FREQ'] != 'A') for x in rows)):
            raise RuntimeError('OECD 数据口径不符')
        rows.sort(key=lambda x: x['TIME_PERIOD'], reverse=True)
    return {'source': 'OECD Education at a Glance 官方 SDMX', 'source_url': r.url, 'area': area, 'age': age, 'sex': sex, 'start': start, 'end': end, 'scope': '对应年龄及性别人群中已达到高等教育（ISCED 2011 级别 5–8）的比例，百分数；非高等教育入学率。空值为缺失非零，保留原始状态。', 'items': rows, 'documentation': 'https://data-explorer.oecd.org/vis?df[ag]=OECD.EDU.IMEP&df[id]=DSD_EAG_LSO_EA%40DF_LSO_NEAC_DISTR_EA&df[vs]=1.0'}
