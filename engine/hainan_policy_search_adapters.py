"""海南省人民政府政策文件库搜索。"""
import release_runtime
import requests
ENDPOINT = 'https://www.hainan.gov.cn/hisearch/list/'

def search(keyword, page=1, field='all'):
    if not isinstance(keyword, str) or not keyword.strip() or len(keyword) > 200:
        raise ValueError('关键词须为 1–200 字')
    if isinstance(page, bool) or not isinstance(page, int) or (not 1 <= page <= 1000):
        raise ValueError('页码须为 1–1000 整数')
    if field not in ('all', 'title'):
        raise ValueError('field 须为 all 或 title')
    params = {'size': 10, 'sort': '', 'keyword': keyword.strip(), 'page': page, 'field': field, 'excludefield': '', 'excludeKeyword': '', 'department': '', 'lawtype': '', 'subject': '', 'daterange': '', 'filetype': '', 'tsfl': '', 'year': ''}
    r = requests.get(ENDPOINT, params=params, timeout=20)
    r.raise_for_status()
    d = r.json()
    if d.get('code') != 0:
        raise RuntimeError('官方搜索服务返回错误')
    data = d.get('data', {})
    items = data.get('data')
    total = data.get('total')
    if not isinstance(items, list) or not isinstance(total, int) or total < 0:
        raise RuntimeError('官方响应结构异常')
    if not items and (page - 1) * 10 < total or len(items) > total:
        raise RuntimeError('总数和页内结果不一致')
    return {'source': '海南省人民政府政策文件库', 'keyword': keyword.strip(), 'field': field, 'page': page, 'total': total, 'items': items, 'notice': '搜索结果可能含转载、历史及其他文件；摘要不保证全文，现行效力须核对原文。'}

def detail(url):
    """读取省政府门户 HTML 正文，不跟随外站或下载附件。"""
    from urllib.parse import urlsplit
    from bs4 import BeautifulSoup
    if not isinstance(url, str):
        raise ValueError('需要正文链接')
    p = urlsplit(url)
    try:
        valid_port = p.port in (None, 80, 443)
    except ValueError:
        valid_port = False
    if p.scheme not in ('http', 'https') or p.hostname != 'www.hainan.gov.cn' or p.username or p.password or (not valid_port) or (not (p.path.startswith('/hainan/') or p.path.startswith('/hn/'))):
        raise ValueError('仅支持海南省政府门户政策文件链接')
    safe = 'https://www.hainan.gov.cn' + p.path + ('?' + p.query if p.query else '')
    r = requests.get(safe, timeout=20, allow_redirects=False)
    r.raise_for_status()
    if r.is_redirect or 'html' not in r.headers.get('Content-Type', '').lower() or len(r.content) > 5000000:
        raise RuntimeError('页面跳转、非 HTML 或过大')
    soup = BeautifulSoup(r.content, 'html.parser')
    node = soup.select_one('#zoom .TRS_Editor, #zoom, .TRS_Editor')
    if not node:
        raise RuntimeError('正文容器未识别')
    text = node.get_text('\n', strip=True)
    if len(text) < 100:
        raise RuntimeError('正文过短，请查原网页')
    return {'url': safe, 'title': soup.title.get_text(' ', strip=True) if soup.title else None, 'text': text, 'notice': '原发布页面；附件、后续修订及当前效力须核对。'}
