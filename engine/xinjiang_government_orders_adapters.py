"""新疆自治区政府令栏目公开标题搜索与正文。"""
import release_runtime
import re
from urllib.parse import urlsplit
import requests
from bs4 import BeautifulSoup
API = 'https://www.xinjiang.gov.cn/interface-cms/qryManuscriptByWebsiteId'

def search(keyword, page=1):
    if not isinstance(keyword, str) or not keyword.strip() or len(keyword) > 200:
        raise ValueError('关键词须为 1–200 字')
    if isinstance(page, bool) or not isinstance(page, int) or (not 1 <= page <= 1000):
        raise ValueError('页码须为 1–1000 整数')
    payload = {'websiteId': '2a4092ca8c2a4255bfec9f13f114aba6', 'channelId': ['ba866337787a44e6bfc770d792425829'], 'pageSize': 15, 'title': keyword.strip(), 'pageNum': page}
    r = requests.post(API, json=payload, timeout=20, allow_redirects=False)
    r.raise_for_status()
    if r.is_redirect:
        raise RuntimeError('官方搜索跳转')
    d = r.json()
    rows = d.get('results')
    total = d.get('totalCount')
    if d.get('Status') != 'success' or d.get('currentPage') != page or (not isinstance(rows, list)) or (not isinstance(total, int)):
        raise RuntimeError('搜索响应异常')
    if not rows and (page - 1) * 15 < total:
        raise RuntimeError('搜索总数与结果矛盾')
    items = []
    for x in rows:
        path = x.get('url', '')
        if not re.fullmatch('/xinjiang/(?:zfl|gzk)/\\d{6}/[a-f0-9]{32}\\.shtml', path):
            raise RuntimeError('结果链接不在已验证范围')
        items.append({'title': x.get('title'), 'url': 'https://www.xinjiang.gov.cn' + path, 'published': x.get('publishedTime'), 'channel': x.get('channelName'), 'memo': x.get('memo')})
    return {'source': '新疆自治区政府令栏目搜索', 'keyword': keyword.strip(), 'page': page, 'total': total, 'items': items, 'notice': '站方结果实测同时包含政府令和规章栏目；请核对现行效力与原文附件。'}

def detail(url):
    if not isinstance(url, str):
        raise ValueError('需要文件链接')
    p = urlsplit(url)
    try:
        valid_port = p.port in (None, 80, 443)
    except ValueError:
        valid_port = False
    if p.scheme not in ('http', 'https') or p.hostname != 'www.xinjiang.gov.cn' or p.username or p.password or (not valid_port) or (not re.fullmatch('/xinjiang/(?:zfl|gzk)/\\d{6}/[a-f0-9]{32}\\.shtml', p.path)):
        raise ValueError('仅支持新疆政府令及规章栏目正文链接')
    safe = 'https://www.xinjiang.gov.cn' + p.path
    r = requests.get(safe, timeout=20, allow_redirects=False)
    r.raise_for_status()
    if r.is_redirect or 'html' not in r.headers.get('Content-Type', '').lower() or len(r.content) > 5000000:
        raise RuntimeError('页面跳转、非 HTML 或过大')
    s = BeautifulSoup(r.content, 'html.parser')
    node = s.select_one('.gknbxq_detail')
    if not node:
        raise RuntimeError('正文容器未识别')
    text = node.get_text('\n', strip=True)
    if len(text) < 300:
        raise RuntimeError('正文过短或为附件公告，请查看原站附件')
    return {'url': safe, 'title': s.title.get_text(' ', strip=True) if s.title else None, 'text': text, 'notice': '请核对现行效力与附件。'}
