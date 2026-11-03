"""OECD 官方季度国民账户的实际 GDP 环比增长率。"""
import release_runtime
import csv, io, re
import requests
BASE = 'https://sdmx.oecd.org/public/rest/data/OECD.SDD.NAD,DSD_NAMAIN1@DF_QNA_EXPENDITURE_GROWTH_OECD,1.1/'

def gdp_growth(area, start='2020-Q1', end=None):
    if not isinstance(area, str) or not re.fullmatch('[A-Z0-9]{2,5}', area):
        raise ValueError('area 须为 OECD 地区代码，例如 USA、DEU 或 OECD')
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
    r = requests.get(BASE + f'Q.Y.{area}.S1..B1GQ......G1.', params=p, timeout=30)
    if r.status_code == 204:
        rows = []
    else:
        r.raise_for_status()
        reader = csv.DictReader(io.StringIO(r.text))
        required = {'TIME_PERIOD', 'OBS_VALUE', 'REF_AREA', 'ADJUSTMENT', 'UNIT_MEASURE', 'TRANSFORMATION'}
        if not reader.fieldnames or not required.issubset(reader.fieldnames):
            raise RuntimeError('OECD 返回的 CSV 列结构异常')
        rows = list(reader)
        if any((x['REF_AREA'] != area or x['ADJUSTMENT'] != 'Y' or x['UNIT_MEASURE'] != 'PC' or (x['TRANSFORMATION'] != 'G1') for x in rows)):
            raise RuntimeError('OECD 返回了预期之外的统计口径')
        rows.sort(key=lambda x: x['TIME_PERIOD'], reverse=True)
    return {'source': 'OECD 季度国民账户官方 SDMX API', 'source_url': r.url, 'area': area, 'start': start, 'end': end, 'scope': '实际 GDP 链式物量、日历及季节调整、环比增长率，百分数，非年化；保留 OECD 原始代码及状态。', 'items': rows, 'documentation': 'https://data-explorer.oecd.org/vis?df[ag]=OECD.SDD.NAD&df[id]=DSD_NAMAIN1%40DF_QNA_EXPENDITURE_GROWTH_OECD&df[vs]=1.1'}
