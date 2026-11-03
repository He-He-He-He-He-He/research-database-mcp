"""国家外汇管理局中国外汇市场交易概况年度工作簿。"""
import release_runtime
import datetime, hashlib, io, re
from urllib.parse import urljoin, urlsplit
import requests, openpyxl
from openpyxl.utils.datetime import from_excel
from bs4 import BeautifulSoup
INDEX = 'https://www.safe.gov.cn/safe/zgwhscjygk/index.html'

def _get(url):
    r = requests.get(url, timeout=25, allow_redirects=False)
    r.raise_for_status()
    if r.is_redirect or len(r.content) > 15000000:
        raise ValueError('响应跳转或过大')
    return r.content

def catalog():
    s = BeautifulSoup(_get(INDEX), 'html.parser')
    items = {}
    for a in s.select('a[href]'):
        m = re.fullmatch('(20\\d{2})年中国外汇市场交易概况', a.get_text(' ', strip=True))
        if not m:
            continue
        u = urljoin(INDEX, a['href'])
        p = urlsplit(u)
        if p.scheme == 'https' and p.hostname == 'www.safe.gov.cn' and re.fullmatch('/safe/\\d{4}/\\d{4}/\\d+\\.html', p.path):
            items[m.group(1)] = {'year': int(m.group(1)), 'url': u}
    if not items:
        raise ValueError('未识别年度目录')
    return {'source': '国家外汇管理局中国外汇市场交易概况', 'source_url': INDEX, 'items': sorted(items.values(), key=lambda x: x['year'], reverse=True), 'note': '年度目录以官网当前内容为准。'}

def table(year, currency='美元', keyword=''):
    if isinstance(year, bool) or not isinstance(year, int) or currency not in ('美元', '人民币'):
        raise ValueError('年份必须为整数，币种为美元或人民币')
    if not isinstance(keyword, str) or len(keyword) > 100:
        raise ValueError('关键词最多100字')
    record = next((x for x in catalog()['items'] if x['year'] == year), None)
    if not record:
        raise ValueError('年度不在目录中')
    s = BeautifulSoup(_get(record['url']), 'html.parser')
    urls = []
    for a in s.select('a[href]'):
        u = urljoin(record['url'], a['href'])
        p = urlsplit(u)
        if '以' + currency + '计价' in a.get_text(' ', strip=True) and p.scheme == 'https' and (p.hostname == 'www.safe.gov.cn') and re.fullmatch('/safe/file/file/\\d{8}/[a-f0-9]+\\.xlsx', p.path):
            urls.append(u)
    if len(urls) != 1:
        raise ValueError('未找到唯一币种工作簿')
    raw = _get(urls[0])
    w = openpyxl.load_workbook(io.BytesIO(raw), data_only=True)
    matches = [s for s in w if '以' + currency + '计价' in s.title]
    if len(matches) != 1:
        raise ValueError('未找到唯一工作表')
    sh = matches[0]
    if sh.max_row > 1000 or sh.max_column > 250:
        raise ValueError('工作表过大')
    vals = list(sh.values)
    if len(vals) < 5 or str(vals[2][0]).strip() != '交易品种':
        raise ValueError('未识别表头')
    periods = []
    for idx, v in enumerate(vals[2][1:], 1):
        if isinstance(v, datetime.datetime):
            p = v.strftime('%Y-%m')
        elif isinstance(v, (int, float)) and (not isinstance(v, bool)) and (35000 < v < 60000):
            p = from_excel(v, w.epoch).strftime('%Y-%m')
        elif isinstance(v, str) and (m := re.fullmatch('(20\\d{2})年\\s*(\\d{1,2})月', v.strip())):
            p = f'{m.group(1)}-{int(m.group(2)):02d}'
        else:
            continue
        if not p.startswith(str(year) + '-'):
            raise ValueError('表头年份不符')
        periods.append((idx, p))
    if not periods:
        raise ValueError('未识别月度表头')
    rows = []
    notes = []
    group = None
    is_note = False
    for i, row in enumerate(vals[3:], 4):
        name = row[0] if row else None
        if not isinstance(name, str) or not name.strip():
            continue
        text = name.strip()
        if text.startswith(('注：', '注:')):
            is_note = True
        if is_note:
            notes.append(text)
            continue
        if re.match('^[一二三四五]、', text):
            group = text
        if keyword and keyword not in text:
            continue
        rows.append({'row': i, 'group': group, 'item_original': name, 'values': {p: row[idx] for idx, p in periods}})
    return {'source': '国家外汇管理局中国外汇市场交易概况', 'year': year, 'currency': currency, 'page_url': record['url'], 'workbook_url': urls[0], 'sha256': hashlib.sha256(raw).hexdigest(), 'unit_original': str(vals[1][0]).strip(), 'periods': [p for _, p in periods], 'rows': rows, 'notes': notes, 'note': '原表仅人民币对外汇交易，不含外汇间交易；银行对客户市场和银行间市场采用不同统计口径，交易量不等于净流入。保留底层数值，显示精度及空值以原表为准。'}
