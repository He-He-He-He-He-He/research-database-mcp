"""Single-page topic catalogue on ZJU Smart Ancient Books public website."""
import release_runtime
import requests
from zju_csab_catalog_pages import validate_page

def search_topics(keyword='', page=1, page_size=5, timeout=20):
    if not isinstance(keyword, str) or len(keyword) > 100:
        raise ValueError('keyword must be a string of at most 100 characters')
    if isinstance(page, bool) or not isinstance(page, int) or (not 1 <= page <= 50):
        raise ValueError('page must be an integer between 1 and 50')
    if isinstance(page_size, bool) or not isinstance(page_size, int) or (not 1 <= page_size <= 20):
        raise ValueError('page_size must be an integer between 1 and 20')
    r = requests.get('https://csab.zju.edu.cn/api/topic/findAllTopic', params={'key': keyword, 'page': page, 'pageSize': page_size}, timeout=timeout)
    r.raise_for_status()
    data = r.json()
    result = data.get('result')
    if str(data.get('code')) != '200' or not isinstance(result, dict) or (not isinstance(result.get('list'), list)):
        raise ValueError('unexpected topic catalogue response')
    validate_page(result, page, page_size)
    return {'source': 'https://csab.zju.edu.cn/', 'attribution': '数据来自智慧古籍平台(https://csab.zju.edu.cn)', 'keyword': keyword, 'total': result.get('total'), 'page': result.get('pageNum'), 'page_size': result.get('pageSize'), 'total_pages': result.get('pages'), 'topics': [{'id': item.get('id'), 'name': item.get('name')} for item in result['list']], 'note': '独立公开平台单页专题目录，不代表馆藏全文；自动化专门许可尚未核实，遵守平台条款。'}
