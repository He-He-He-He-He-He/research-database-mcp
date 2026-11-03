"""国家外汇局银行代客涉外收付款分地区月度官方原表。"""
import release_runtime
import hashlib, io, re
from urllib.parse import urljoin, urlsplit
import requests, openpyxl
from bs4 import BeautifulSoup
PAGE = 'https://www.safe.gov.cn/safe/2018/0419/8806.html'

def _get(url):
    r = requests.get(url, timeout=25, allow_redirects=False)
    r.raise_for_status()
    if r.is_redirect or len(r.content) > 15000000:
        raise ValueError('响应跳转或过大')
    return r.content

def catalog():
    s = BeautifulSoup(_get(PAGE), 'html.parser')
    items = []
    for a in s.select('#content a[href]'):
        title = a.get_text(' ', strip=True)
        u = urljoin(PAGE, a['href'])
        p = urlsplit(u)
        m = re.fullmatch('(20\\d{2})年银行代客涉外收付款数据（分地区）', title)
        if m and p.scheme == 'https' and (p.hostname == 'www.safe.gov.cn') and re.fullmatch('/safe/file/file/\\d{8}/[a-f0-9]+\\.xlsx', p.path):
            items.append({'year': int(m.group(1)), 'title': title, 'url': u})
    if not items:
        raise ValueError('未识别分地区工作簿目录')
    return {'source': '国家外汇管理局', 'source_url': PAGE, 'items': items, 'note': '仅列公开分地区 XLSX；时间序列 XLS 另见原站，此接口不解析。'}

def table(year, month, area='', keyword=''):
    if isinstance(year, bool) or not isinstance(year, int) or isinstance(month, bool) or (not isinstance(month, int)) or (not 1 <= month <= 12):
        raise ValueError('年份和月份参数无效')
    if not isinstance(area, str) or not isinstance(keyword, str) or max(len(area), len(keyword)) > 100:
        raise ValueError('筛选条件无效')
    item = next((x for x in catalog()['items'] if x['year'] == year), None)
    if not item:
        raise ValueError('所选年度不在官方目录')
    raw = _get(item['url'])
    if not raw.startswith(b'PK'):
        raise ValueError('文件不是 XLSX')
    wb = openpyxl.load_workbook(io.BytesIO(raw), data_only=True)
    matches = [s for s in wb if s.title.strip() == str(month) + '月']
    if len(matches) != 1:
        raise ValueError('该月份尚未发布或工作表名称变化')
    sh = matches[0]
    if sh.max_row > 500 or sh.max_column > 250:
        raise ValueError('表格尺寸异常')
    values = list(sh.values)
    if len(values) < 5 or values[2][0].strip() != '项目':
        raise ValueError('未识别表头')
    headers = [str(x).strip() if x is not None else '' for x in values[2]]
    pos = [i for i, h in enumerate(headers[1:], 1) if h and (not area or area == h)]
    if not pos:
        raise ValueError('地区未在该月表头中，请先查询不筛选的表')
    rows = []
    notes = []
    group = None
    in_notes = False
    for i, row in enumerate(values[3:], 4):
        label = row[0] if row else None
        if not isinstance(label, str) or not label.strip():
            continue
        if re.match('^[一二三]、', label.strip()):
            group = label.strip()
        if label.strip().startswith(('注：', '注:')):
            in_notes = True
        if in_notes:
            notes.append(label.strip())
            continue
        if keyword and keyword not in label:
            continue
        rows.append({'row': i, 'group': group, 'item_original': label, 'values': {headers[k]: row[k] for k in pos}})
    return {'source': '国家外汇管理局', 'source_url': PAGE, 'workbook_url': item['url'], 'sha256': hashlib.sha256(raw).hexdigest(), 'year': year, 'month': month, 'sheet': sh.title, 'unit_original': str(values[1][0]).strip(), 'areas': [headers[i] for i in pos], 'rows': rows, 'notes': notes, 'note': '银行代客涉外收付款不含银行自身及现钞收付，不等同结售汇或国际收支全口径；保留工作簿底层数值，显示精度以原表为准，注意区域口径和附注。'}
