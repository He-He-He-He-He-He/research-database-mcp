"""国家外汇管理局银行结售汇时间序列原表。"""
import release_runtime
import hashlib
import re
from io import BytesIO
from urllib.parse import urljoin
from bs4 import BeautifulSoup
from openpyxl import load_workbook
from openpyxl.utils.datetime import from_excel
from safe_balance_payments_adapters import _get
PAGE = 'https://www.safe.gov.cn/safe/2023/0215/22329.html'

def series(frequency='月度', currency='美元', keyword=''):
    if frequency not in ('年度', '月度') or currency not in ('美元', '人民币'):
        raise ValueError('频率为年度/月度，计价为美元/人民币')
    soup = BeautifulSoup(_get(PAGE), 'html.parser')
    links = [a for a in soup.select('#content a[href]') if '时间序列' in a.get_text() and '.xlsx' in a['href'].lower()]
    if len(links) != 1:
        raise RuntimeError('未识别时间序列工作簿')
    url = urljoin(PAGE, links[0]['href'])
    if not url.startswith('https://www.safe.gov.cn/'):
        raise RuntimeError('工作簿域名不符合预期')
    raw = _get(url)
    w = load_workbook(BytesIO(raw), data_only=True, read_only=True)
    s = w[f'以{currency}计价（{frequency}）']
    rows = s.iter_rows(min_row=4, max_row=43, max_col=250, values_only=True)
    head = next(rows)
    cols = []
    for i, v in enumerate(head[2:], 2):
        if frequency == '年度' and isinstance(v, str) and re.fullmatch('\\d{4}年', v):
            cols.append((i, v[:-1], v))
        if frequency == '月度' and isinstance(v, (int, float)) and (35000 < v < 60000):
            d = from_excel(v, w.epoch)
            cols.append((i, d.strftime('%Y-%m'), v))
    if not cols or len({x[1] for x in cols}) != len(cols):
        raise RuntimeError('时间列无法识别或重复')
    result = []
    last_parent = None
    for i, row in enumerate(rows, 5):
        a, b = (row[0], row[1])
        if a is None and b is None:
            continue
        if a is not None:
            last_parent = str(a).strip()
        item = str(a).strip() if a is not None else None
        if keyword and keyword not in (item or last_parent or '') and (keyword not in str(b or '')):
            continue
        result.append({'row': i, 'item': item, 'continuation_of': last_parent if item is None else None, 'subitem': b, 'values': {key: row[pos] for pos, key, _ in cols}})
    month_sheet = w[f'以{currency}计价（月度）']
    monthly = next(month_sheet.iter_rows(min_row=4, max_row=4, max_col=250, values_only=True))
    dates = [from_excel(x, w.epoch) for x in monthly[2:] if isinstance(x, (int, float)) and 35000 < x < 60000]
    return {'source_page': PAGE, 'workbook_url': url, 'sha256': hashlib.sha256(raw).hexdigest(), 'sheet': s.title, 'unit': s.cell(3, 1).value, 'periods': [{'period': p, 'original_header': v} for _, p, v in cols], 'latest_month': max(dates).strftime('%Y-%m') if dates else None, 'rows': result}
