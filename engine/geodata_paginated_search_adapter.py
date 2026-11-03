"""国家地球系统科学数据中心公开数据集检索，分页。"""
import release_runtime
import requests
from geodata_search_adapters import FIELDS, ENDPOINT

def search(keyword, page=1, size=10):
    if not isinstance(keyword, str) or not keyword.strip() or len(keyword) > 100:
        raise ValueError('请输入1–100字符关键词')
    if any((isinstance(v, bool) or not isinstance(v, int) for v in (page, size))) or not 1 <= page <= 200 or (not 1 <= size <= 50):
        raise ValueError('页码1–200，每页1–50')
    q = {'word': keyword.strip(), 'pageSize': size, 'page': page, 'skip': (page - 1) * size, 'take': size}
    r = requests.get(ENDPOINT, params=q, timeout=25, allow_redirects=False)
    r.raise_for_status()
    if r.is_redirect or len(r.content) > 10000000:
        raise ValueError('响应跳转或过大')
    data = r.json().get('op_read')
    if not isinstance(data, dict) or not isinstance(data.get('data'), list):
        raise ValueError('未识别数据集检索结果')
    return {'source': '国家地球系统科学数据中心', 'source_url': 'https://www.geodata.cn/data/', 'keyword': keyword.strip(), 'page': page, 'page_size': size, 'total': data.get('total'), 'items': [{k: row.get(k) for k in FIELDS} for row in data['data']], 'note': '仅公开目录元数据，时间、开放及下载状态以原站为准；分页可能随数据更新变化，详情与下载权限尚未验证。'}
