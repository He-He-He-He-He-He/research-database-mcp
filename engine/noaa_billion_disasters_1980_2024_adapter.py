"""NOAA's retired 1980-2024 US billion-dollar weather disaster event record."""
import release_runtime
import csv, io
import requests
URL = 'https://www.ncei.noaa.gov/access/billions/events-US-1980-2024.csv'
DOCS = 'https://www.nesdis.noaa.gov/news/billion-dollar-weather-and-climate-disasters'
NOTE = 'NOAA 美国十亿美元天气气候灾害事件目录，产品停止更新，覆盖截至 2024 年，不可用于推断 2025 年以后无灾害。仅覆盖损失达到 10 亿美元门槛的美国灾害，损失是估计值；费用原表单位为百万美元。CPI-Adjusted Cost 使用 2024 CPI 价格调整，Unadjusted Cost 为未调整额；不得混加或当成保险赔款。年份按事件开始日期筛选，跨年事件未按实际发生年份拆分；死亡数及各字段按原始字符串保留。'

def events(year=None, keyword='', offset=0, limit=50, session=None):
    if year is not None and (isinstance(year, bool) or not isinstance(year, int) or (not 1980 <= year <= 2024)):
        raise ValueError('开始年份须在 1980 至 2024')
    if not isinstance(keyword, str) or len(keyword) > 200:
        raise ValueError('关键词最多 200 字符')
    if isinstance(offset, bool) or not isinstance(offset, int) or offset < 0:
        raise ValueError('起始行须为非负整数')
    if isinstance(limit, bool) or not isinstance(limit, int) or (not 1 <= limit <= 1000):
        raise ValueError('每页数量须为 1 至 1000')
    with (session or requests).get(URL, headers={'Accept': '*/*', 'User-Agent': 'PersonalResearchToolkit/1.0'}, timeout=35, stream=True) as r:
        r.raise_for_status()
        b = bytearray()
        for c in r.iter_content(65536):
            b.extend(c)
            if len(b) > 5 * 1024 * 1024:
                raise ValueError('NOAA 原表超过 5 MiB')
        url = r.url
    try:
        rows = list(csv.reader(io.StringIO(bytes(b).decode('utf-8-sig'), newline='')))
    except (UnicodeError, csv.Error) as exc:
        raise ValueError('NOAA CSV 解析失败') from exc
    if len(rows) < 3 or rows[2][:3] != ['Name', 'Disaster', 'Begin Date']:
        raise ValueError('NOAA CSV 表头异常')
    term = keyword.strip().casefold()
    matched = [row for row in rows[3:] if len(row) >= 7 and (year is None or row[2].startswith(str(year))) and (not term or any((term in c.casefold() for c in row)))]
    return {'source': 'NOAA NCEI U.S. Billion-Dollar Weather and Climate Disasters', 'source_url': url, 'documentation': DOCS, 'note': NOTE, 'source_header': rows[:2], 'columns': rows[2], 'total_matched_rows': len(matched), 'offset': offset, 'limit': limit, 'returned_rows': len(matched[offset:offset + limit]), 'next_offset': offset + limit if offset + limit < len(matched) else None, 'truncated': offset + limit < len(matched), 'rows': matched[offset:offset + limit]}
