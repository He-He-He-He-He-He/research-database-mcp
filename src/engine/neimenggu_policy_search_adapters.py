"""内蒙古自治区政府政策文件库检索。"""
import release_runtime
import requests
ENDPOINT = 'https://www.nmg.gov.cn/nmsearch/openSearch/zcwjk/getZcList.do'

def search(keyword, page=1):
    if not isinstance(keyword, str) or not keyword.strip() or len(keyword) > 200:
        raise ValueError('关键词须为 1–200 字')
    if isinstance(page, bool) or not isinstance(page, int) or (not 1 <= page <= 1000):
        raise ValueError('页码须为 1–1000 整数')
    params = {'cdesc': '', 'chnId': '', 'cityName': '', 'docno': '', 'docnotype': '', 'doctype': '0', 'keywords': keyword.strip(), 'pageNum': page, 'pageSize': 8, 'publisher': '', 'sort': 'other', 'wenzhong': '', 'zcYear': '', 'startTime': '', 'endTime': '', 'validity': '', 'bsfwfl': '', 'position': '1', 'searchTag': 'all'}
    r = requests.get(ENDPOINT, params=params, timeout=20)
    r.raise_for_status()
    d = r.json()
    if d.get('state') != 200:
        raise RuntimeError('官方搜索服务错误')
    data = d.get('data', {})
    items = data.get('data')
    total = data.get('total')
    if not isinstance(items, list) or not isinstance(total, int) or data.get('pageNum') != page:
        raise RuntimeError('官方搜索响应结构或页码异常')
    if not items and (page - 1) * 8 < total or len(items) > total:
        raise RuntimeError('总数与页内结果不一致')
    return {'source': '内蒙古自治区人民政府政策文件库', 'keyword': keyword.strip(), 'page': page, 'total': total, 'items': [{k: v for k, v in row.items() if k != 'zc_doccontent'} for row in items], 'notice': '原站默认搜索范围；结果含多级政府不同性质及历史文件，状态与原文需另核查。'}
