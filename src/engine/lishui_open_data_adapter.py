"""丽水市数据开放平台目录及无条件开放资源网页样本。"""
import release_runtime
import re
import requests
BASE = 'https://data.lishui.gov.cn/api-gateway/jpaas-lssjkf-web-server/interface/opendata/'

def _json(method, path, **kw):
    r = requests.request(method, BASE + path, timeout=30, allow_redirects=False, **kw)
    r.raise_for_status()
    if r.is_redirect:
        raise RuntimeError('平台重定向，未返回预期数据')
    try:
        d = r.json()
    except ValueError as e:
        raise RuntimeError('平台响应非 JSON') from e
    if not isinstance(d, dict) or d.get('code') != '200' or (not isinstance(d.get('data'), dict)) or (not isinstance(d['data'].get('result'), dict)):
        raise RuntimeError('平台返回错误或结构异常')
    return d['data']['result']

def search(keyword='', page=1, size=10):
    if not isinstance(keyword, str) or len(keyword) > 100:
        raise ValueError('关键词不得超过100字')
    if isinstance(page, bool) or not isinstance(page, int) or page < 1 or isinstance(size, bool) or (not isinstance(size, int)) or (not 1 <= size <= 50):
        raise ValueError('页码或页大小无效')
    p = {'keyword': keyword, 'pageNo': page, 'pageSize': size, 'historyFlag': '0'}
    d = _json('POST', 'queryOpenBaseData', json=p)
    rows = d.get('dataList')
    total = d.get('totalCount')
    if not isinstance(rows, list) or not isinstance(total, int) or isinstance(total, bool) or (total < 0) or (len(rows) > size):
        raise RuntimeError('目录分页结构异常')
    fields = ('baseid', 'title', 'content', 'deptname', 'isOpen', 'data_count', 'createdate', 'modifydate', 'domainname', 'areaname')
    return {'source': '丽水市数据开放平台', 'keyword': keyword, 'page': page, 'size': size, 'total': total, 'items': [{k: r.get(k) for k in fields} for r in rows], 'note': '官网搜索关键词可能匹配摘要等字段，非仅标题；isOpen=0 为无条件开放，1 为受限开放；结果仅为目录，非已取得完整数据。'}

def preview(baseid, title):
    if not isinstance(baseid, str) or not re.fullmatch('[0-9]{1,20}', baseid):
        raise ValueError('目录 ID 无效')
    if not isinstance(title, str) or not 1 <= len(title) <= 100:
        raise ValueError('需提供完整资源标题')
    listing = _json('POST', 'queryOpenBaseData', json={'keyword': title, 'isOpen': '0', 'pageNo': 1, 'pageSize': 50, 'historyFlag': '0'})
    rows = listing.get('dataList')
    if not isinstance(rows, list) or not any((r.get('baseid') == baseid and r.get('title') == title and (r.get('isOpen') == '0') for r in rows)):
        raise ValueError('目录第一页未核实完全匹配的无条件开放资源')
    d = _json('GET', 'queryBaseDataDetail', params={'baseDataId': baseid})
    if d.get('baseid') != baseid or d.get('title') != title or d.get('isOpen') != '0' or (not isinstance(d.get('paramsList'), list)):
        raise RuntimeError('官网资源详情不匹配或无有效预览')
    return {'source': '丽水市数据开放平台', 'id': baseid, 'title': title, 'provider': d.get('deptname'), 'catalog_url': 'https://data.lishui.gov.cn/', 'open_type': '无条件开放', 'data_count': d.get('data_count'), 'modifydate': d.get('modifydate'), 'rows': d['paramsList'], 'fields': d.get('resourceFieldInfoList'), 'note': '官方网页直接展示的样本，不代表全量或最新数据；保留原始值，单位及指标定义请核对字段说明和原始资料。'}
