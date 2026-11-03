"""陕西省政府网站政策文件搜索和本站正文。"""
import release_runtime
from urllib.parse import urlsplit
import requests
from bs4 import BeautifulSoup
ENDPOINT = 'https://www.shaanxi.gov.cn/irs/front/search'

def search(keyword, page=1):
    if not isinstance(keyword, str) or not keyword.strip() or len(keyword) > 200:
        raise ValueError('关键词须为 1–200 字')
    if isinstance(page, bool) or not isinstance(page, int) or (not 1 <= page <= 1000):
        raise ValueError('页码须为 1–1000 的整数')
    q = keyword.strip()
    body = {'tenantId': '16711', 'searchWord': q, 'dataTypeId': 17050, 'historySearchWords': [], 'orderBy': 'related', 'searchBy': 'title', 'granularity': 'ALL', 'pageNo': str(page), 'pageSize': 10, 'filters': [], 'configTenantId': '16711', 'customFilter': {'operator': 'and', 'properties': [{'property': 'site_id', 'operator': 'eq', 'value': 11}], 'filters': []}}
    r = requests.post(ENDPOINT, json=body, timeout=20)
    r.raise_for_status()
    d = r.json()
    if d.get('success') is not True:
        raise RuntimeError('陕西官方搜索服务报错')
    data = d['data']
    pager = data['pager']
    rows = data['middle']['listAndBox']
    if data['searchInfo'].get('searchWord') != q or pager.get('pageNo') != page or (not isinstance(rows, list)):
        raise RuntimeError('查询或分页不匹配')
    items = []
    for row in rows:
        if row.get('type') == 'DATA' and isinstance(row.get('data'), dict):
            items.append({k: v for k, v in row['data'].items() if k != 'table-5'})
    total = pager.get('total')
    if not isinstance(total, int) or total < 0 or (not items and (page - 1) * 10 < total):
        raise RuntimeError('返回总数与结果不一致')
    return {'source': '陕西省政府网站文件分类', 'keyword': q, 'pager': pager, 'items': items, 'notice': '标题检索本站文件分类，涵盖地方性法规、规章及其他文件；状态与正文应另行核对。'}

def detail(url):
    if not isinstance(url, str):
        raise ValueError('需要正文链接')
    p = urlsplit(url)
    try:
        valid_port = p.port in (None, 80, 443)
    except ValueError:
        valid_port = False
    if p.scheme not in ('http', 'https') or p.hostname != 'www.shaanxi.gov.cn' or p.username or p.password or (not valid_port) or (not p.path.startswith('/zfxxgk/')):
        raise ValueError('仅支持陕西省政府信息公开本站链接')
    safe = 'https://www.shaanxi.gov.cn' + p.path + ('?' + p.query if p.query else '')
    r = requests.get(safe, timeout=20, allow_redirects=False)
    r.raise_for_status()
    if r.is_redirect or 'html' not in r.headers.get('Content-Type', '').lower() or len(r.content) > 5000000:
        raise RuntimeError('页面跳转、非 HTML 或过大')
    s = BeautifulSoup(r.content, 'html.parser')
    node = s.select_one('.pages_content')
    if not node:
        raise RuntimeError('正文容器未识别')
    text = node.get_text('\n', strip=True)
    if len(text) < 100:
        raise RuntimeError('正文过短，请查原网页')
    return {'url': safe, 'text': text, 'title': s.title.get_text(' ', strip=True) if s.title else None, 'notice': '发布页面；当前效力与附件须核对。'}
