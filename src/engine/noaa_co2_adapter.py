"""NOAA GML 月均大气 CO2：全球海洋表面或夏威夷观测系列。"""
import release_runtime
import csv, io, re
import requests
BASE = 'https://gml.noaa.gov/webdata/ccgg/trends/co2/'
FILES = {'global': 'co2_mm_gl.csv', 'hawaii': 'co2_mm_mlo.csv'}

def co2_monthly(series='global', start='2000-01', end=None, limit=36):
    if series not in FILES:
        raise ValueError('series 仅支持 global 或 hawaii')
    for v in (start, end):
        if v is not None and (not isinstance(v, str) or not re.fullmatch('\\d{4}-(?:0[1-9]|1[0-2])', v)):
            raise ValueError('月份须为 YYYY-MM')
    if start and end and (start > end):
        raise ValueError('开始月份不能晚于结束月份')
    if isinstance(limit, bool) or not isinstance(limit, int) or (not 1 <= limit <= 1000):
        raise ValueError('limit 必须为 1 至 1000')
    r = requests.get(BASE + FILES[series], timeout=25)
    r.raise_for_status()
    reader = csv.DictReader(io.StringIO('\n'.join((line for line in r.content.decode('utf-8-sig').splitlines() if line and (not line.startswith('#'))))))
    required = {'year', 'month', 'average'} | ({'average_unc', 'trend', 'trend_unc'} if series == 'global' else {'deseasonalized', 'ndays', 'sdev', 'unc'})
    if not reader.fieldnames or not required.issubset(reader.fieldnames):
        raise RuntimeError('NOAA CSV 列结构异常')
    items = []
    for row in reader:
        try:
            ym = f"{int(row['year']):04d}-{int(row['month']):02d}"
        except (ValueError, TypeError, KeyError):
            raise RuntimeError('NOAA 日期格式异常') from None
        if start and ym < start or (end and ym > end):
            continue
        row['period'] = ym
        items.append(row)
    items.sort(key=lambda v: v['period'], reverse=True)
    scope = '全球海洋表面月均大气 CO2 干空气摩尔分数及去季节趋势，单位 ppm；非全球排放量。' if series == 'global' else '夏威夷背景站月均大气 CO2 干空气摩尔分数，单位 ppm；非全球平均。2022-12 至 2023-07-04 因火山喷发改在 Maunakea 测量。负的天数或不确定度是数据缺失或插值标记，不能作实际测量。'
    return {'source': 'NOAA Global Monitoring Laboratory', 'series': series, 'start': start, 'end': end, 'total_matching': len(items), 'limit': limit, 'truncated': len(items) > limit, 'items': items[:limit], 'scope': scope + '结果按月份倒序；如 truncated 为 true 可提高 limit（最多1000）或缩小时间范围。数据可回溯修订，使用时引用 NOAA GML。', 'download_url': BASE + FILES[series], 'documentation': 'https://gml.noaa.gov/ccgg/trends/gl_data.html' if series == 'global' else 'https://gml.noaa.gov/ccgg/trends/data.html'}
