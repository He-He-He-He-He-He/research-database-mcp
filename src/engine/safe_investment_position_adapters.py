"""国家外汇管理局国际投资头寸表时间序列。"""
import release_runtime
import hashlib
import re
from io import BytesIO
from urllib.parse import urljoin
from bs4 import BeautifulSoup
from openpyxl import load_workbook
from safe_balance_payments_adapters import _get
PAGE = 'https://www.safe.gov.cn/safe/2019/0627/13520.html'

def positions(frequency='季度', currency='美元', keyword=''):
    """取得官方最新存量表，按工作表和项目名称筛选。"""
    if frequency not in ('年度', '季度') or currency not in ('美元', 'SDR'):
        raise ValueError('频率为年度/季度，货币为美元/SDR')
    soup = BeautifulSoup(_get(PAGE), 'html.parser')
    links = [a for a in soup.select('#content a[href]') if '.xlsx' in a['href'].lower()]
    if len(links) != 1:
        raise RuntimeError('未识别唯一工作簿，页面可能变化')
    url = urljoin(PAGE, links[0]['href'])
    if not url.startswith('https://www.safe.gov.cn/'):
        raise RuntimeError('工作簿域名不符')
    raw = _get(url)
    book = load_workbook(BytesIO(raw), read_only=True, data_only=True)
    sheet = book[f'{frequency}IIP({currency})']
    header = next(sheet.iter_rows(min_row=3, max_row=3, values_only=True))
    cols = [(i, v) for i, v in enumerate(header) if isinstance(v, str) and re.fullmatch('\\d{4}年(?:[369]月)?末', v)]
    if not cols:
        raise RuntimeError('未识别时点表头')
    rows = []
    notes = []
    in_notes = False
    for idx, row in enumerate(sheet.iter_rows(min_row=5, values_only=True), 5):
        title = row[0]
        if not isinstance(title, str) or not title.strip():
            continue
        if title.strip().startswith('备注'):
            in_notes = True
            continue
        if in_notes:
            notes.append(title.strip())
            continue
        if keyword and keyword not in title:
            continue
        rows.append({'row': idx, 'item': title.strip(), 'values': {name: row[pos] if pos < len(row) else None for pos, name in cols}})
    return {'source_page': PAGE, 'workbook_url': url, 'sha256': hashlib.sha256(raw).hexdigest(), 'sheet': sheet.title, 'unit': sheet.cell(2, 1).value, 'periods': [v for _, v in cols], 'notes': notes, 'rows': rows}
