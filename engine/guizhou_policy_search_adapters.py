"""贵州省政府政策文件库标题检索。"""
import release_runtime
import re
import requests
JS = 'https://www.guizhou.gov.cn/material/2026/zcwjk2025_main_v2.js'
ENDPOINT = 'https://www.guizhou.gov.cn/irs/front/list'

def search(keyword, page=1):
    if not isinstance(keyword, str) or not keyword.strip() or len(keyword) > 200:
        raise ValueError('关键词须为 1–200 字')
    if isinstance(page, bool) or not isinstance(page, int) or (not 1 <= page <= 1000):
        raise ValueError('页码须为 1–1000 整数')
    js = requests.get(JS, timeout=20)
    js.raise_for_status()
    ids = []
    for key in 'ABC':
        m = re.search('const\\s+Channel_' + key + '\\s*=\\s*"([0-9,]+)"', js.text)
        if not m:
            raise RuntimeError('官方文件分类参数发生变化')
        ids.extend(m.group(1).split(','))
    if not 1 <= len(ids) <= 1000:
        raise RuntimeError('官方分类参数异常')
    body = {'pageNo': page, 'pageSize': 2, 'tenantId': '', 'tableName': 't_179d132472b', 'sorts': [], 'searchFields': [{'fieldName': 'f_202163261554', 'searchWord': keyword.strip(), 'minimumShouldMatch': '3<75%'}], 'customFilter': {'operator': 'or', 'properties': [{'property': 'f_202163742494', 'operator': 'eq', 'value': x} for x in ids]}}
    r = requests.post(ENDPOINT, json=body, timeout=20)
    r.raise_for_status()
    d = r.json()
    if d.get('success') is not True:
        raise RuntimeError('官方搜索服务出错')
    data = d.get('data', {})
    records = data.get('list')
    pager = data.get('pager', {})
    if not isinstance(records, list) or pager.get('pageNo') != page or (not isinstance(pager.get('total'), int)):
        raise RuntimeError('官方返回分页结构异常')
    fields = ('f_202163261554', 'doc_pub_url', 'f_202163332978', 'f_202163281171', 'save_time', 'f_2021617230443', 'f_202163462560')
    items = [{k: row.get(k) for k in fields} for row in records]
    if not items and (page - 1) * 2 < pager['total']:
        raise RuntimeError('总数与结果不一致')
    return {'source': '贵州省政府政策文件库', 'keyword': keyword.strip(), 'pager': pager, 'items': items, 'notice': '站方按标题近似匹配省市县文件，每次两条；内容类型混杂，效力与原文应另查。'}
