"""住建部城乡建设统计年鉴 ZIP：原表目录、XLS 表格单元格读取。"""
import release_runtime
import ast, hashlib, io, json, re, zipfile, sys
from pathlib import Path
from urllib.parse import urljoin, urlsplit
import requests
sys.path.insert(0, str(Path(__file__).resolve().parent / 'vendor'))
import xlrd
from bs4 import BeautifulSoup
BASE = 'https://www.mohurd.gov.cn'
INDEX = BASE + '/gongkai/fdzdgknr/sjfb/tjxx/jstjnj/'
API = BASE + '/api-gateway/jpaas-publish-server/front/page/build/unit'

def _get(url, cap=40000000, **kwargs):
    with requests.get(url, timeout=(15, 60), allow_redirects=False, stream=True, **kwargs) as r:
        r.raise_for_status()
        if r.is_redirect:
            target = urljoin(url, r.headers.get('Location', ''))
            p = urlsplit(target)
            if p.scheme != 'https' or p.hostname != 'www.mohurd.gov.cn' or (not p.path.startswith('/cms_files/filemanager/')) or (not p.path.endswith('.zip')):
                raise ValueError('非预期下载重定向')
            return _get(target, cap)
        data = bytearray()
        for chunk in r.iter_content(65536):
            data.extend(chunk)
            if len(data) > cap:
                raise ValueError('文件超过大小上限')
        return bytes(data)

def catalog():
    soup = BeautifulSoup(_get(INDEX, 2000000), 'html.parser')
    script = soup.select_one('script[querydata]')
    if not script or script.get('url') != '/api-gateway/jpaas-publish-server/front/page/build/unit':
        raise ValueError('目录组件改变')
    params = ast.literal_eval(script['querydata'])
    params['paramJson'] = json.dumps({'pageNo': 1, 'pageSize': 100})
    data = json.loads(_get(API, params=params))
    if not data.get('success'):
        raise ValueError('目录请求未成功')
    soup = BeautifulSoup(data['data']['html'], 'html.parser')
    items = []
    for a in soup.select('a[href]'):
        title = a.get_text(' ', strip=True)
        m = re.fullmatch('(20\\d{2})年城乡建设统计年鉴', title)
        u = urljoin(INDEX, a['href'])
        p = urlsplit(u)
        if m and p.scheme == 'https' and (p.hostname == 'www.mohurd.gov.cn') and (p.path == '/api-gateway/jpaas-web-server/front/document/download' or (p.path.startswith('/cms_files/filemanager/mohurdold/file/') and p.path.endswith(('.zip', '.rar')))):
            items.append({'year': int(m[1]), 'title': title, 'download_url': u, 'format': 'rar' if p.path.endswith('.rar') else 'zip'})
    if not items:
        raise ValueError('未识别城乡建设年鉴')
    return {'source': '住房城乡建设部城乡建设统计年鉴', 'source_url': INDEX, 'items': items, 'note': '目录最多取前 100 项；RAR 仅列地址，不解析。'}

def _archive(year):
    if isinstance(year, bool) or not isinstance(year, int):
        raise ValueError('year 必须为整数')
    item = next((x for x in catalog()['items'] if x['year'] == year), None)
    if not item:
        raise ValueError('年份不在官方目录中')
    if item['format'] != 'zip':
        raise ValueError('该年为 RAR，仅提供下载地址，不解析')
    raw = _get(item['download_url'])
    if not raw.startswith(b'PK\x03\x04'):
        raise ValueError('来源文件不是 ZIP')
    z = zipfile.ZipFile(io.BytesIO(raw), metadata_encoding='gbk')
    if len(z.infolist()) > 1500:
        raise ValueError('压缩包文件数超限')
    return (item, raw, z)

def files(year, keyword=''):
    if not isinstance(keyword, str) or len(keyword) > 100:
        raise ValueError('关键词最多 100 字')
    item, raw, z = _archive(year)
    entries = [{'name': x.filename, 'bytes': x.file_size} for x in z.infolist() if not x.is_dir() and x.filename.lower().endswith('.xls') and (keyword in x.filename)]
    return {'source': '住房城乡建设部城乡建设统计年鉴', **item, 'sha256': hashlib.sha256(raw).hexdigest(), 'keyword': keyword, 'files': entries, 'note': '只列 XLS 原表；无需向文件系统解压。'}

def rows(year, filename, sheet_index=0, keyword='', limit=100):
    if not isinstance(filename, str) or not filename or len(filename) > 500:
        raise ValueError('filename 应为目录中原始文件名')
    if isinstance(sheet_index, bool) or not isinstance(sheet_index, int) or sheet_index < 0:
        raise ValueError('sheet_index 应为非负整数')
    if not isinstance(keyword, str) or len(keyword) > 100:
        raise ValueError('关键词最多 100 字')
    if isinstance(limit, bool) or not isinstance(limit, int) or (not 1 <= limit <= 500):
        raise ValueError('limit 应为 1–500')
    item, raw, z = _archive(year)
    names = [x for x in z.infolist() if x.filename == filename and (not x.is_dir()) and x.filename.lower().endswith('.xls')]
    if len(names) != 1 or names[0].file_size > 15000000:
        raise ValueError('XLS 不存在、重复或超过大小上限')
    book = xlrd.open_workbook(file_contents=z.read(names[0]))
    if sheet_index >= book.nsheets:
        raise ValueError('工作表索引越界')
    s = book.sheet_by_index(sheet_index)
    if s.nrows > 10000 or s.ncols > 500:
        raise ValueError('表格过大')
    hits = []
    count = 0
    for i in range(s.nrows):
        cells = s.row_values(i)
        if keyword in ' '.join(map(str, cells)):
            count += 1
            if len(hits) < limit:
                hits.append({'row': i + 1, 'cells': cells})
    return {'source': '住房城乡建设部城乡建设统计年鉴', **item, 'sha256': hashlib.sha256(raw).hexdigest(), 'filename': filename, 'sheet_names': book.sheet_names(), 'sheet_index': sheet_index, 'header_rows': [{'row': i + 1, 'cells': s.row_values(i)} for i in range(min(8, s.nrows))], 'matched_rows': count, 'rows': hits, 'note': '按原始单元格返回，行号从 1 起；不填充合并单元格，不能把空白当作零，须核对原表单位、标题及脚注。'}
