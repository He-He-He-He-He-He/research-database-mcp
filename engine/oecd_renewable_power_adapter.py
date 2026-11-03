"""OECD 可再生电力发电占比年度数据。"""
import release_runtime
import csv, io, re
import requests
BASE = 'https://sdmx.oecd.org/public/rest/data/OECD.ENV.EPI,DSD_GG@DF_GREEN_GROWTH,1.2/'

def renewable_power_share(area, start='2000', end=None):
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
    r = requests.get(BASE + f'{area}.A.RE_NRG.PT_GEN_EL._T', params=p, timeout=30)
    if r.status_code == 204:
        rows = []
    else:
        r.raise_for_status()
        reader = csv.DictReader(io.StringIO(r.text))
        required = {'REF_AREA', 'FREQ', 'MEASURE', 'UNIT_MEASURE', 'ACTIVITY', 'TIME_PERIOD', 'OBS_VALUE', 'OBS_STATUS'}
        if not reader.fieldnames or not required.issubset(reader.fieldnames):
            raise RuntimeError('OECD CSV 列结构异常')
        rows = list(reader)
        if any((x['REF_AREA'] != area or x['FREQ'] != 'A' or x['MEASURE'] != 'RE_NRG' or (x['UNIT_MEASURE'] != 'PT_GEN_EL') or (x['ACTIVITY'] != '_T') for x in rows)):
            raise RuntimeError('OECD 统计口径不符')
        rows.sort(key=lambda x: x['TIME_PERIOD'], reverse=True)
    return {'source': 'OECD Green Transition 官方 SDMX', 'source_url': r.url, 'area': area, 'start': start, 'end': end, 'scope': '年度可再生电力发电量占全部电力发电量的百分比；不是总能源消费占比。保留原始估算及修订状态。', 'items': rows, 'documentation': 'https://data-explorer.oecd.org/vis?df[ag]=OECD.ENV.EPI&df[id]=DSD_GG%40DF_GREEN_GROWTH&df[vs]=1.2'}
