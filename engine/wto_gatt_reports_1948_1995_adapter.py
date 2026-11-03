"""WTO GATT dispute reports official CSV, one row per report."""
import release_runtime
import csv, io
import requests
URL = 'https://gatt-disputes.wto.org/reports/csv'
CATALOG = 'https://gatt-disputes.wto.org/index.php/reports'
NOTE = 'WTO 整理的 GATT 历史争端报告记录，不是现代 WTO 争端清单。这是报告级目录，同一 GD 争端可能有多条报告记录，不能把记录行数当成争端数。报告文号、发布日期、页数和采纳状态按原始字符串保留，空白不是零或否。报告已采纳并不自动等于某一方胜诉，应核对具体报告原文与争端程序。'

def reports(keyword='', case_id='', offset=0, limit=50, session=None):
    if not isinstance(keyword, str) or len(keyword) > 200:
        raise ValueError('关键词最多 200 字符')
    if not isinstance(case_id, str) or len(case_id) > 30:
        raise ValueError('无效争端编号')
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
                raise ValueError('报告目录大于 5 MiB')
        url = r.url
    try:
        rows = list(csv.reader(io.StringIO(bytes(b).decode('utf-8-sig'), newline='')))
    except (UnicodeError, csv.Error) as exc:
        raise ValueError('官方 CSV 解析失败') from exc
    if not rows or rows[0][:2] != ['GD', 'Dispute title'] or 'Report' not in rows[0]:
        raise ValueError('官方 CSV 表头异常')
    term = keyword.strip().casefold()
    case = case_id.strip().casefold()
    matched = [row for row in rows[1:] if row and (not case or row[0].casefold() == case) and (not term or any((term in c.casefold() for c in row)))]
    return {'source': 'World Trade Organization GATT Dispute Reports', 'source_url': url, 'catalog': CATALOG, 'note': NOTE, 'columns': rows[0], 'total_matched_rows': len(matched), 'offset': offset, 'limit': limit, 'rows': matched[offset:offset + limit]}
