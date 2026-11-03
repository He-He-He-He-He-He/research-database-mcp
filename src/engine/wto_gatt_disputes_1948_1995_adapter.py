"""WTO GATT dispute database official CSV, 1948–1995."""
import release_runtime
import csv, io
import requests
URL = 'https://gatt-disputes.wto.org/disputes/csv'
CATALOG = 'https://gatt-disputes.wto.org/index.php/disputes'
NOTE = 'WTO 整理的 1948–1995 年 GATT 争端历史目录，不是 1995 年后的 WTO 争端清单。申诉、被申诉、第三方、报告和采纳状态照原文保留；空白不是 No，存在特殊表述如拒绝采纳。成立报告或采纳不等于某方胜诉；需要阅读原始争端报告与具体法律过程。关键词和年份对官方完整 CSV 在本机筛选，不是服务端搜索；结果可能随官方更新。'

def disputes(keyword='', year=None, offset=0, limit=50, session=None):
    if not isinstance(keyword, str) or len(keyword) > 200:
        raise ValueError('关键词最多 200 字符')
    if year is not None and (isinstance(year, bool) or not isinstance(year, int) or (not 1948 <= year <= 1995)):
        raise ValueError('年份须在 1948 至 1995')
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
                raise ValueError('争端目录大于 5 MiB')
        url = r.url
    try:
        rows = list(csv.reader(io.StringIO(bytes(b).decode('utf-8-sig'), newline='')))
    except (UnicodeError, csv.Error) as exc:
        raise ValueError('官方 CSV 解析失败') from exc
    if not rows or rows[0][:2] != ['GD', 'Complainants'] or 'Year' not in rows[0]:
        raise ValueError('官方 CSV 表头异常')
    year_col = rows[0].index('Year')
    term = keyword.strip().casefold()
    matched = [row for row in rows[1:] if (year is None or (len(row) > year_col and row[year_col] == str(year))) and (not term or any((term in c.casefold() for c in row)))]
    return {'source': 'World Trade Organization GATT Disputes Database', 'source_url': url, 'catalog': CATALOG, 'note': NOTE, 'columns': rows[0], 'total_matched_rows': len(matched), 'offset': offset, 'limit': limit, 'rows': matched[offset:offset + limit]}
