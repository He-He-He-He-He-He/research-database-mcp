"""可持续发展大数据国际研究中心数据共享平台元数据检索。"""
import release_runtime
import requests
URL = 'https://data.casearth.cn/api/dataset/search'

def search(keyword='', page=1, page_size=10):
    if not isinstance(keyword, str) or len(keyword) > 150:
        raise ValueError('关键词无效')
    if isinstance(page, bool) or not isinstance(page, int) or (not 1 <= page <= 1000):
        raise ValueError('页码无效')
    if isinstance(page_size, bool) or not isinstance(page_size, int) or (not 1 <= page_size <= 50):
        raise ValueError('每页须为1–50条')
    p = {'q': keyword.strip(), 'cids': '', 'tags': '', 'itemTypes': '', 'pageNum': page, 'pageSize': page_size}
    r = requests.get(URL, params=p, timeout=30)
    r.raise_for_status()
    d = r.json()
    if d.get('code') != 200 or not isinstance(d.get('rows'), list):
        raise ValueError('平台返回非预期数据')
    return {'source': '可持续发展大数据国际研究中心数据共享服务平台', 'source_url': r.url, 'query': keyword, 'page': page, 'page_size': page_size, 'reported_total': d.get('total'), 'items': d['rows'], 'note': '这是公开网页使用的元数据检索接口；测试发现跨页可能重复，请按记录 oi 去重，动态排序还可能导致遗漏。该服务实测英语关键词有结果、部分中文词返回空；元数据不代表实体数据可免登录下载。'}
