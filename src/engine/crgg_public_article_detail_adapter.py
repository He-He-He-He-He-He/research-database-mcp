"""国别区域与全球治理平台公开文章详情，仅读取页面题录。"""
import release_runtime
import re
import requests
from bs4 import BeautifulSoup
URL = 'https://www.crggcn.com/skwx_crgg/initDatabaseDetail'

def article(content_id, expected_title):
    content_id = str(content_id)
    if not re.fullmatch('[0-9]{1,16}', content_id):
        raise ValueError('content_id 须为数字')
    if not isinstance(expected_title, str) or not 1 <= len(expected_title.strip()) <= 300 or any((ord(c) < 32 for c in expected_title)):
        raise ValueError('须提供检索结果原始题名')
    r = requests.get(URL, params={'siteId': '25', 'contentId': content_id, 'contentType': 'literature'}, timeout=25)
    r.raise_for_status()
    p = BeautifulSoup(r.content, 'html.parser')
    titles = p.select('div.title')
    if len(titles) != 1 or titles[0].get_text(' ', strip=True) != expected_title.strip():
        raise RuntimeError('详情题名与预期不符')
    if not re.search('databaseDetailCounter\\?ContentID=' + re.escape(content_id) + '&ContentType=literature(?:&|["\\\'])', r.text):
        raise RuntimeError('详情编号未确认')
    labels = {'来源：': 'source_book', '作者：': 'authors', '出版日期：': 'published_raw', '关键词：': 'keywords'}
    data = {v: None for v in labels.values()}
    for block in p.select('div.article_index'):
        spans = block.find_all('span', recursive=False)
        if not spans:
            continue
        label = spans[0].get_text(' ', strip=True)
        if label not in labels:
            continue
        value = block.get_text(' ', strip=True)[len(label):].strip()
        if data[labels[label]] is not None:
            raise RuntimeError('重复的详情字段')
        data[labels[label]] = value or None
    return {'source': '国别区域与全球治理平台公开文章题录', 'content_id': content_id, 'title': expected_title.strip(), **data, 'note': '匿名公开页面题录，核对详情编号与检索题名；未读取正文，学校身份与逐篇全文权限未验证。'}
