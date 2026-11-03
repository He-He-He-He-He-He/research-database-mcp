"""Bounded read-only access to ZJU Smart Ancient Books public work catalogue.

This is a separate public platform, not a subscription library full-text API.
"""
import release_runtime
import requests
ENDPOINT = 'https://csab.zju.edu.cn/api/work/findAllWork'
SOURCE = 'https://csab.zju.edu.cn/'
ATTRIBUTION = '数据来自智慧古籍平台(https://csab.zju.edu.cn)'

def search_works(keyword='', page=1, page_size=5, timeout=20):
    """Return one catalogue page; do not retrieve texts or images."""
    if not isinstance(keyword, str) or len(keyword) > 100:
        raise ValueError('keyword must be a string of at most 100 characters')
    if isinstance(page, bool) or not isinstance(page, int) or (not 1 <= page <= 50):
        raise ValueError('page must be an integer between 1 and 50')
    if isinstance(page_size, bool) or not isinstance(page_size, int) or (not 1 <= page_size <= 20):
        raise ValueError('page_size must be an integer between 1 and 20')
    response = requests.get(ENDPOINT, params={'key': keyword, 'page': page, 'pageSize': page_size, 'sort': '', 'place': ''}, timeout=timeout)
    response.raise_for_status()
    payload = response.json()
    result = payload.get('result')
    if str(payload.get('code')) != '200' or not isinstance(result, dict) or (not isinstance(result.get('list'), list)):
        raise ValueError('unexpected catalogue response')
    total = result.get('totalCount')
    pages = result.get('totalPage')
    rows = result['list']
    if type(total) is not int or total < 0 or type(pages) is not int or (pages != (total + page_size - 1) // page_size) or (result.get('currPage') != page) or (result.get('pageSize') != page_size) or (len(rows) != min(page_size, max(0, total - (page - 1) * page_size))) or any((not isinstance(item, dict) for item in rows)):
        raise ValueError('catalogue pagination or records inconsistent')
    keys = ('id', 'name', 'author', 'dynasty', 'type', 'reel', 'sectionName', 'isVisitor')
    return {'source': SOURCE, 'attribution': ATTRIBUTION, 'keyword': keyword, 'page': result.get('currPage'), 'page_size': result.get('pageSize'), 'total': result.get('totalCount'), 'total_pages': result.get('totalPage'), 'works': [{k: item.get(k) for k in keys} for item in result['list']], 'note': '独立公开平台的单页题录，非馆藏全文接口；未核实目录完整性及自动化专门许可，遵守平台条款。'}
