"""科技资源标识服务平台公开网页的科学资源元数据搜索。"""
import release_runtime
import requests
URL = 'https://www.cstr.cn/openapi/v3/api/search'

def search(query, page=1, page_size=10, resource_types=None):
    if not isinstance(query, str) or not 1 <= len(query.strip()) <= 150:
        raise ValueError('查询词须为1–150字符')
    if isinstance(page, bool) or not isinstance(page, int) or (not 1 <= page <= 1000):
        raise ValueError('page无效')
    if page_size not in (1, 2, 5, 10, 20, 40, 80, 100) or isinstance(page_size, bool):
        raise ValueError('page_size须为1、2、5、10、20、40、80或100')
    if resource_types is None:
        resource_types = []
    if not isinstance(resource_types, list) or len(resource_types) > 20 or any((not isinstance(x, str) or not x.isdigit() or len(x) > 3 for x in resource_types)):
        raise ValueError('资源类型代码无效')
    body = {'page_num': page, 'page_size': page_size, 'query': query.strip(), 'resource_type': resource_types, 'publisher_name': [], 'identifier': None, 'prefix': '', 'registrant': None}
    r = requests.post(URL, json=body, timeout=30)
    r.raise_for_status()
    d = r.json()
    if d.get('code') != 200 or not isinstance(d.get('items'), list):
        raise ValueError('平台搜索失败：' + str(d.get('detail', '未知响应'))[:200])
    return {'source': '中国科学院计算机网络信息中心科技资源标识服务平台', 'source_url': 'https://www.cstr.cn/', 'request_url': URL, 'page': page, 'page_size': page_size, 'reported_total': d.get('total'), 'reported_total_pages': d.get('total_pages'), 'items': d['items'], 'note': '调用平台公开网页使用的搜索接口，非需开发者密钥的正式详情API；元数据及资源链接不表示实体文件开放下载。搜索总数可能受平台上限限制；结果随收录更新变化。'}
