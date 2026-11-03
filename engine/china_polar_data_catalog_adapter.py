"""国家极地科学数据中心公开数据集元数据目录。"""
import release_runtime
import uuid
import requests
BASE = 'https://datacenter.chinare.org.cn/api/dif/'

def search(keyword='', page=1, page_size=10):
    if not isinstance(keyword, str) or len(keyword) > 150:
        raise ValueError('关键词无效')
    if isinstance(page, bool) or not isinstance(page, int) or (not 1 <= page <= 1000):
        raise ValueError('页码无效')
    if isinstance(page_size, bool) or not isinstance(page_size, int) or (not 1 <= page_size <= 50):
        raise ValueError('每页须为1–50条')
    p = {'search': keyword.strip(), 'apply_pub_status': 'published', 'pagesize': page_size, 'page': page}
    r = requests.get(BASE, params=p, timeout=30)
    r.raise_for_status()
    d = r.json()
    if not isinstance(d.get('results'), list) or not isinstance(d.get('count'), int):
        raise ValueError('非预期数据目录响应')
    return {'source': '国家极地科学数据中心', 'source_url': r.url, 'count': d['count'], 'page': page, 'items': d['results'], 'note': '返回公开目录元数据；共享方式依记录和网站规定，未验证实体文件下载。'}

def detail(identifier):
    if not isinstance(identifier, str):
        raise ValueError('数据集ID无效')
    try:
        identifier = str(uuid.UUID(identifier))
    except ValueError:
        raise ValueError('数据集ID须为UUID') from None
    r = requests.get(BASE + identifier + '/', timeout=30)
    r.raise_for_status()
    d = r.json()
    if not isinstance(d, dict) or d.get('id') != identifier:
        raise ValueError('非预期详情响应')
    return {'source': '国家极地科学数据中心', 'source_url': r.url, 'data': d, 'note': '公开元数据详情；文件获取条件以平台与数据集许可为准。'}
