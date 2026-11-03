"""深圳市政府规范性文件官方搜索索引；不等同完整政策库。"""
import release_runtime
import json
import requests
from bs4 import BeautifulSoup

def search(keyword, page=1):
    if not isinstance(keyword, str) or not keyword.strip() or len(keyword) > 200:
        raise ValueError('关键词须为 1–200 字')
    if isinstance(page, bool) or not isinstance(page, int) or (not 1 <= page <= 1000):
        raise ValueError('页码须为 1–1000 整数')
    p = {'callback': 'researchCallback', 'page': page, 'pagesize': 20, 'isgkml': 1, 'text': keyword.strip(), 'order': 0, 'including_url_doc': 1, 'including_attach_doc': 1, 'classify_main_name': '', 'classify_mains': '749', 'classify_mains_excluded': '', 'position': 'title'}
    r = requests.get('https://search.gd.gov.cn/jsonp/site/755001', params=p, headers={'Referer': 'https://www.sz.gov.cn/'}, timeout=20, allow_redirects=False)
    r.raise_for_status()
    if r.is_redirect:
        raise RuntimeError('搜索服务跳转')
    body = r.text
    prefix = 'researchCallback('
    if not body.startswith(prefix) or not body.endswith(')'):
        raise RuntimeError('搜索服务 JSONP 格式异常')
    try:
        d = json.loads(body[len(prefix):-1])
        rows = d['results']
        count = d['count']
    except (ValueError, KeyError, TypeError) as e:
        raise RuntimeError('搜索响应异常') from e
    if not isinstance(rows, list) or not isinstance(count, int):
        raise RuntimeError('搜索响应结构异常')
    if count == 0 or not rows:
        raise RuntimeError('搜索返回空结果；服务曾出现不稳定，不能区分无匹配与异常')
    if len(rows) > 20 or (page - 1) * 20 >= count:
        raise RuntimeError('搜索页与总数矛盾')
    items = [{'title': BeautifulSoup(x.get('title', ''), 'html.parser').get_text(' ', strip=True), 'url': x.get('url'), 'published': x.get('pub_time'), 'snippet': BeautifulSoup(x.get('content', ''), 'html.parser').get_text(' ', strip=True)} for x in rows]
    return {'source': '深圳市政府规范性文件搜索索引', 'keyword': keyword.strip(), 'page': page, 'total': count, 'items': items, 'notice': '搜索索引可能不完整或滞后；文件现行状态需到原站核验。'}
