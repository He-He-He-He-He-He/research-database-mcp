"""重庆市政府政策文件库默认检索。"""
import release_runtime
from datetime import datetime
from zoneinfo import ZoneInfo
import requests
ENDPOINT = 'https://www.cq.gov.cn/irs/front/list'

def search(keyword, page=1):
    if not isinstance(keyword, str) or not keyword.strip() or len(keyword) > 200:
        raise ValueError('关键词须为 1–200 字')
    if isinstance(page, bool) or not isinstance(page, int) or (not 1 <= page <= 1000):
        raise ValueError('页码须为 1–1000 整数')
    now = datetime.now(ZoneInfo('Asia/Shanghai')).strftime('%Y-%m-%d %H:%M:%S')
    title = {'operator': 'or', 'properties': [{'property': 'f_202121500898', 'operator': 'eq', 'value': keyword.strip()}], 'filters': []}
    dates = {'operator': 'or', 'properties': [{'property': k, 'operator': 'gte', 'value': now} for k in ('f_202146838317', 'f_202146235090')], 'filters': [{'operator': 'and', 'properties': [{'property': k, 'operator': 'eq', 'value': None} for k in ('f_202146838317', 'f_202146235090')]}]}
    body = {'customFilter': {'operator': 'and', 'properties': [], 'filters': [title, dates]}, 'sorts': [], 'tableName': 't_1775cd018c6', 'tenantId': '7', 'pageSize': 10, 'pageNo': page}
    r = requests.post(ENDPOINT, json=body, timeout=20)
    r.raise_for_status()
    d = r.json()
    if d.get('success') is not True:
        raise RuntimeError('官方搜索服务错误')
    data = d.get('data', {})
    pager = data.get('pager', {})
    rows = data.get('list')
    total = pager.get('total')
    if not isinstance(rows, list) or pager.get('pageNo') != page or (not isinstance(total, int)) or isinstance(total, bool) or (total < 0):
        raise RuntimeError('响应结构、总数或页码不匹配')
    if len(rows) > 10 or len(rows) > total:
        raise RuntimeError('返回总数与页内结果不一致')
    if not rows and (page - 1) * 10 < pager['total']:
        raise RuntimeError('返回总数与页内结果不一致')
    items = [{k: v for k, v in row.items() if k != 'f_202142777829'} for row in rows]
    return {'source': '重庆市政府政策文件库', 'keyword': keyword.strip(), 'pager': pager, 'items': items, 'notice': '按官网标题查询及默认时效字段条件筛选；返回含多类政策文件，不能代替对现行效力及原文的核查。'}
