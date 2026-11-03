"""辽宁省政府政策文件库检索与省门户正文。"""
import release_runtime
from urllib.parse import urlsplit
import requests
from bs4 import BeautifulSoup
ENDPOINT = 'https://api.so-gov.cn/query/s'

def search(keyword, page=1):
    if not isinstance(keyword, str) or not keyword.strip() or len(keyword) > 200:
        raise ValueError('关键词须为 1–200 字')
    if isinstance(page, bool) or not isinstance(page, int) or (not 1 <= page <= 1000):
        raise ValueError('页码须为 1–1000 整数')
    params = {'siteCode': '2100000037', 'tab': 'zc', 'qt': keyword.strip(), 'keyPlace': 1, 'sort': 'dateDesc', 'fileType': '', 'timeOption': 0, 'locationCode': '210000000000', 'page': page, 'pageSize': 20}
    r = requests.post(ENDPOINT, data=params, timeout=20)
    r.raise_for_status()
    d = r.json()
    if d.get('ok') is not True:
        raise RuntimeError('官方搜索服务错误：' + str(d.get('msg')))
    docs = d.get('resultDocs')
    total = d.get('totalHits')
    query = d.get('queryTextObject', {})
    if not isinstance(docs, list) or not isinstance(total, int) or query.get('originQt') != keyword.strip():
        raise RuntimeError('搜索响应结构或关键词异常')
    if not docs and (page - 1) * 20 < total or len(docs) > total:
        raise RuntimeError('搜索总数与结果不一致')
    return {'source': '辽宁省政府政策文件库', 'keyword': keyword.strip(), 'page': page, 'total': total, 'items': docs, 'notice': '默认政策分类标题检索，含不同状态文件；应核对原文、附件和后续修改。'}

def detail(url):
    if not isinstance(url, str):
        raise ValueError('需要原文链接')
    p = urlsplit(url)
    try:
        valid_port = p.port in (None, 80, 443)
    except ValueError:
        valid_port = False
    if p.scheme not in ('http', 'https') or p.hostname != 'www.ln.gov.cn' or p.username or p.password or (not valid_port) or (not p.path.startswith('/web/zwgkx/')):
        raise ValueError('仅支持辽宁省政府门户政务公开链接')
    safe = 'https://www.ln.gov.cn' + p.path + ('?' + p.query if p.query else '')
    r = requests.get(safe, timeout=20, allow_redirects=False)
    r.raise_for_status()
    if r.is_redirect or 'html' not in r.headers.get('Content-Type', '').lower() or len(r.content) > 5000000:
        raise RuntimeError('页面跳转、非 HTML 或过大')
    soup = BeautifulSoup(r.content, 'html.parser')
    node = soup.select_one('.zfwj_detail .content')
    if not node:
        raise RuntimeError('正文容器未识别')
    text = node.get_text('\n', strip=True)
    if len(text) < 100:
        raise RuntimeError('正文过短，请查原网页')
    return {'url': safe, 'title': soup.title.get_text(' ', strip=True) if soup.title else None, 'text': text, 'notice': '发布页面；附件及当前效力须核查。'}
