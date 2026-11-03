"""NOAA GML globally averaged surface atmospheric methane monthly series."""
import release_runtime
import re
import requests
URL = 'https://gml.noaa.gov/webdata/ccgg/trends/ch4/ch4_mm_gl.txt'

def monthly(start_year=2020, end_year=2026):
    start_year, end_year = (int(start_year), int(end_year))
    if not 1983 <= start_year <= end_year <= 2100:
        raise ValueError('Require 1983 <= start_year <= end_year <= 2100')
    response = requests.get(URL, timeout=30)
    response.raise_for_status()
    if len(response.content) > 2000000:
        raise ValueError('Unexpected NOAA file size')
    raw = response.content.decode('utf-8')
    if 'CH4 expressed as a mole fraction' not in raw or 'average_unc' not in raw:
        raise ValueError('Unexpected NOAA data format')
    created = re.search('^# File Creation:\\s*(.+)$', raw, re.M)
    rows = []
    for line in raw.splitlines():
        if not line.strip() or line.lstrip().startswith('#'):
            continue
        cols = line.split()
        if len(cols) != 7:
            raise ValueError('Unexpected NOAA data row')
        year, month = (int(cols[0]), int(cols[1]))
        if start_year <= year <= end_year:
            vals = [float(x) for x in cols[2:]]
            rows.append({'year': year, 'month': month, 'decimal_year': vals[0], 'average_ppb': vals[1], 'average_uncertainty_ppb': None if vals[2] < 0 else vals[2], 'deseasonalized_trend_ppb': vals[3], 'trend_uncertainty_ppb': None if vals[4] < 0 else vals[4], 'raw_values': dict(zip(('decimal_year', 'average', 'average_unc', 'trend', 'trend_unc'), cols[2:]))})
    return {'source': URL, 'series': 'NOAA GML global monthly mean atmospheric CH4', 'unit': 'nanomol/mol dry air (ppb)', 'file_creation': created.group(1) if created else None, 'note': 'Recent data are subject to revision; null uncertainty means not yet calculated.', 'rows': rows}

def methane_monthly(start='2000-01', end=None, limit=36):
    for value in (start, end):
        if value is not None and (not isinstance(value, str) or not re.fullmatch('\\d{4}-(?:0[1-9]|1[0-2])', value)):
            raise ValueError('月份须为 YYYY-MM')
    if start and end and (start > end):
        raise ValueError('开始月份不能晚于结束月份')
    if isinstance(limit, bool) or not isinstance(limit, int) or (not 1 <= limit <= 1000):
        raise ValueError('limit 必须为 1 至 1000')
    result = monthly(int(start[:4]), int(end[:4]) if end else 2100)
    items = []
    for row in result['rows']:
        period = f"{row['year']:04d}-{row['month']:02d}"
        if period >= start and (not end or period <= end):
            items.append({**row, 'period': period})
    items.sort(key=lambda row: row['period'], reverse=True)
    return {'source': 'NOAA Global Monitoring Laboratory', 'start': start, 'end': end, 'total_matching': len(items), 'limit': limit, 'truncated': len(items) > limit, 'items': items[:limit], 'scope': '结果按月份倒序；truncated 为 true 时可提高 limit（最多1000）或缩小月份范围。全球海洋表面大气甲烷月均干空气摩尔分数，单位 ppb；浓度不等于排放量，缺失不确定度不是零。', 'download_url': URL, 'file_creation': result['file_creation']}
