"""国家自然科学基金青岛海洋科学资料共享服务中心公开元数据。"""
import release_runtime
from urllib.parse import urljoin
import re, requests
from bs4 import BeautifulSoup
BASE = 'https://www.nsfcodc.cn/'

def search(keyword, page=1):
    if not isinstance(keyword, str) or not 1 <= len(keyword.strip()) <= 100:
        raise ValueError('关键词无效')
    if isinstance(page, bool) or not isinstance(page, int) or (not 1 <= page <= 1000):
        raise ValueError('页码无效')
    r = requests.get(BASE + 'database/metadata-service.jsp', params={'key': keyword.strip(), 'nowPage': page}, timeout=30)
    r.raise_for_status()
    s = BeautifulSoup(r.content, 'html.parser')
    if not s.find('form', id='dataForm'):
        raise ValueError('未找到数据搜索表单，页面可能变化或被拦截')
    items = []
    for a in s.select('a[href*="metadatanews-detail-"]'):
        title = a.select_one('.tit')
        description = a.select_one('.con')
        if title and re.fullmatch('/database/metadatanews-detail-\\d+\\.htm', a.get('href', '')):
            items.append({'title': title.get_text(' ', strip=True), 'description': description.get_text(' ', strip=True) if description else '', 'detail_url': urljoin(BASE, a['href'])})
    return {'source': '国家自然科学基金青岛海洋科学资料共享服务中心', 'source_url': r.url, 'query': keyword, 'page': page, 'items': items, 'note': '依据公开网页搜索结果解析元数据，空结果不证明无相关数据。数据下载和授权未验证。'}

def detail(identifier):
    if isinstance(identifier, bool) or not isinstance(identifier, int) or (not 1 <= identifier <= 999999999):
        raise ValueError('ID须为正整数')
    r = requests.get(BASE + 'database/metadatanews-detail-' + str(identifier) + '.htm', timeout=30)
    r.raise_for_status()
    s = BeautifulSoup(r.content, 'html.parser')
    box = s.select_one('.data_detail01 .box')
    title = box.select_one('.tit') if box else None
    body = box.select_one('.myart') if box else None
    if not title or not body:
        raise ValueError('详情结构异常或页面未找到')
    return {'source': '国家自然科学基金青岛海洋科学资料共享服务中心', 'source_url': r.url, 'title': title.get_text(' ', strip=True), 'text': body.get_text('\n', strip=True), 'note': '公开元数据详情，数据文件权限以原站为准。'}
