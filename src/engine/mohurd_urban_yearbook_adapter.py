"""住建部城市建设统计年鉴官方 XLS 原表检索。"""
import release_runtime
import ast, hashlib, json, re, sys
from pathlib import Path
from urllib.parse import urljoin, urlsplit
import requests
sys.path.insert(0, str(Path(__file__).resolve().parent / 'vendor'))
import xlrd
from bs4 import BeautifulSoup
BASE = 'https://www.mohurd.gov.cn'
INDEX = BASE + '/gongkai/fdzdgknr/sjfb/tjxx/jstjnj/'
API = BASE + '/api-gateway/jpaas-publish-server/front/page/build/unit'

def _get(url, cap=30000000, **kwargs):
    with requests.get(url, timeout=50, allow_redirects=False, stream=True, **kwargs) as r:
        r.raise_for_status()
        if r.is_redirect:
            target = urljoin(url, r.headers.get('Location', ''))
            p = urlsplit(target)
            if p.scheme != 'https' or p.hostname != 'www.mohurd.gov.cn' or (not p.path.startswith('/cms_files/filemanager/')) or (not p.path.endswith('.xls')):
                raise ValueError('非预期下载重定向')
            return _get(target, cap)
        data = bytearray()
        for chunk in r.iter_content(65536):
            data.extend(chunk)
            if len(data) > cap:
                raise ValueError('文件超出上限')
        return bytes(data)

def catalog():
    soup = BeautifulSoup(_get(INDEX), 'html.parser')
    script = soup.select_one('script[querydata]')
    if not script or script.get('url') != '/api-gateway/jpaas-publish-server/front/page/build/unit':
        raise ValueError('目录组件改变')
    params = ast.literal_eval(script['querydata'])
    params['paramJson'] = json.dumps({'pageNo': 1, 'pageSize': 100})
    payload = json.loads(_get(API, params=params))
    if not payload.get('success'):
        raise ValueError('目录请求未成功')
    soup = BeautifulSoup(payload['data']['html'], 'html.parser')
    out = []
    for a in soup.select('a[href]'):
        title = a.get_text(' ', strip=True)
        m = re.fullmatch('(20\\d{2})年城市建设统计年鉴', title)
        u = urljoin(INDEX, a['href'])
        p = urlsplit(u)
        if m and p.scheme == 'https' and (p.hostname == 'www.mohurd.gov.cn') and (p.path == '/api-gateway/jpaas-web-server/front/document/download' or (p.path.startswith('/cms_files/filemanager/mohurdold/file/') and p.path.endswith(('.xls', '.rar')))):
            out.append({'year': int(m[1]), 'title': title, 'download_url': u, 'format': 'rar' if p.path.endswith('.rar') else 'xls'})
    if not out:
        raise ValueError('未识别官方年鉴')
    return {'source': '住房城乡建设部城市建设统计年鉴', 'source_url': INDEX, 'items': out, 'note': '最多取前 100 项目录；具体数据年份以原表为准。'}

def _book(year):
    if isinstance(year, bool) or not isinstance(year, int):
        raise ValueError('year 须为整数')
    item = next((i for i in catalog()['items'] if i['year'] == year), None)
    if not item:
        raise ValueError('该年度不在当前目录中')
    if item['format'] != 'xls':
        raise ValueError('该年度为 RAR 压缩包，目前只提供下载地址，不解析')
    raw = _get(item['download_url'])
    if not raw.startswith(b'\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1'):
        raise ValueError('原文件不是预期 XLS')
    return (item, raw, xlrd.open_workbook(file_contents=raw))

def sheets(year):
    item, raw, book = _book(year)
    return {'source': '住房城乡建设部城市建设统计年鉴', **item, 'sha256': hashlib.sha256(raw).hexdigest(), 'sheets': [{'index': i, 'name': s.name, 'title': str(s.cell_value(0, 0)) if s.nrows and s.ncols else '', 'rows': s.nrows, 'columns': s.ncols} for i, s in enumerate(book.sheets())], 'note': '工作表索引从 0 开始；保留原文件核对多行表头及脚注。'}

def search(year, sheet_index, keyword='', limit=100):
    if isinstance(sheet_index, bool) or not isinstance(sheet_index, int) or sheet_index < 0:
        raise ValueError('sheet_index 须为非负整数')
    if not isinstance(keyword, str) or len(keyword) > 100:
        raise ValueError('关键词至多 100 字')
    if isinstance(limit, bool) or not isinstance(limit, int) or (not 1 <= limit <= 500):
        raise ValueError('limit 须为 1–500')
    item, raw, book = _book(year)
    if sheet_index >= book.nsheets:
        raise ValueError('工作表索引超出范围')
    s = book.sheet_by_index(sheet_index)
    if s.nrows > 10000 or s.ncols > 500:
        raise ValueError('工作表尺寸超限')
    rows = []
    count = 0
    for i in range(s.nrows):
        vals = s.row_values(i)
        if keyword in ' '.join(map(str, vals)):
            count += 1
            if len(rows) < limit:
                rows.append({'row': i + 1, 'cells': vals})
    return {'source': '住房城乡建设部城市建设统计年鉴', **item, 'sha256': hashlib.sha256(raw).hexdigest(), 'sheet_index': sheet_index, 'sheet_name': s.name, 'header_rows': [{'row': i + 1, 'cells': s.row_values(i)} for i in range(min(5, s.nrows))], 'matched_rows': count, 'rows': rows, 'note': '原始单元格值，行号从 1 起；合并单元格不填充，表头和脚注须对照原始 XLS，空值不是零。各年分类、范围和修订可能变化。'}
