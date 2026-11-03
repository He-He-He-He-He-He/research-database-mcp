"""绍兴市公共数据开放平台目录和无条件开放的网页预览。"""
import release_runtime
import re
import requests
BASE = 'https://data.sx.gov.cn/athena/catalog/'

def _call(method, path, **kw):
    r = requests.request(method, BASE + path, timeout=30, allow_redirects=False, **kw)
    r.raise_for_status()
    if r.is_redirect:
        raise RuntimeError('官网请求被重定向')
    try:
        d = r.json()
    except ValueError as e:
        raise RuntimeError('官网响应非 JSON') from e
    if not isinstance(d, dict) or d.get('code') != '1' or 'data' not in d:
        raise RuntimeError('官网返回错误或结构异常')
    return d['data']

def search(keyword='', page=1, size=10):
    if not isinstance(keyword, str) or len(keyword) > 100:
        raise ValueError('关键词不能超过100字')
    if isinstance(page, bool) or not isinstance(page, int) or page < 1 or isinstance(size, bool) or (not isinstance(size, int)) or (not 1 <= size <= 50):
        raise ValueError('页码或页大小无效')
    q = {'pageNum': page, 'pageSize': size, 'deptId': '', 'domainId': '', 'isDownload': '', 'uncode': '', 'scene': '', 'fieldType': '', 'updateFrequent': '', 'content': '', 'orderDefault': '', 'isCatalog': '', 'searchType': 1 if keyword else '', 'searchString': keyword}
    d = _call('POST', 'page', json=q)
    if not isinstance(d, dict) or not isinstance(d.get('rows'), list) or (not isinstance(d.get('total'), int)) or isinstance(d.get('total'), bool) or (len(d['rows']) > size):
        raise RuntimeError('官网分页结构异常')
    fields = ('iid', 'title', 'content', 'deptname', 'domain', 'dataSize', 'dataUpdatedate', 'updateTime', 'publishTime')
    return {'source': '绍兴市公共数据开放平台', 'keyword': keyword, 'page': page, 'size': size, 'total': d['total'], 'items': [{k: x.get(k) for k in fields} for x in d['rows']], 'note': '目录中开放条件须在详情核对，官网搜索和分页可能有边界行为；目录总数不等于已获取的数据。'}

def preview(iid):
    if not isinstance(iid, str) or not re.fullmatch('[1-9][0-9]{0,12}', iid):
        raise ValueError('目录 ID 无效')
    d = _call('GET', 'getDetails', params={'dataId': iid})
    if not isinstance(d, dict) or str(d.get('baseDataId')) != iid or (not isinstance(d.get('downloadDataInfo'), dict)):
        raise RuntimeError('官网详情不匹配或无开放状态')
    if d['downloadDataInfo'].get('openCondition') != '无条件开放':
        raise ValueError('仅支持详情明确无条件开放的资源')
    rows = _call('POST', 'getData', json={'dataId': iid})
    if not isinstance(rows, list) or not rows or (not all((isinstance(x, list) for x in rows))):
        raise RuntimeError('官网未返回有效预览')
    return {'source': '绍兴市公共数据开放平台', 'id': iid, 'title': d.get('title'), 'provider': d.get('deptName'), 'data_count': d.get('dataCount'), 'update_time': d.get('dataUpdateDate'), 'open_condition': '无条件开放', 'fields': d['downloadDataInfo'].get('tableParams'), 'rows': rows, 'url': 'https://data.sx.gov.cn/kf/open/table/detail/' + iid, 'note': '官网网页预览可能是样本，部分实测表格疑似字段错位；保留原值，请对照原始表格核验字段、单位、口径和统计时期。目录更新时间不代表数据实际时期。'}
