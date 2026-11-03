"""中国视听大数据公开日榜、周榜。"""
import release_runtime
import json
import re
import subprocess
from urllib.parse import urlencode
BASE = 'https://www.cavbd.cn/prod-api/cvb/'

def _get(path, params=None):
    url = BASE + path + ('?' + urlencode(params) if params else '')
    p = release_runtime.run(['curl', '--fail', '--silent', '--show-error', '--location', '--max-time', '25', url], capture_output=True, text=True, timeout=30)
    if p.returncode:
        raise RuntimeError('中国视听大数据请求失败: ' + p.stderr.strip())
    try:
        r = json.loads(p.stdout)
    except ValueError as exc:
        raise RuntimeError('返回非 JSON，可能受限或网站改版') from exc
    if r.get('code') != 200 or not isinstance(r.get('rows'), list):
        raise RuntimeError('官网返回异常: ' + str(r.get('msg')))
    total = r.get('total')
    rows = r['rows']
    if type(total) is not int or total < 0 or len(rows) > total:
        raise RuntimeError('官网返回的总数与记录数矛盾')
    if params and 'pageNum' in params and ('pageSize' in params):
        page, size = (params['pageNum'], params['pageSize'])
        if len(rows) > size:
            raise RuntimeError('官网返回记录数超过每页数量')
        if rows and (page - 1) * size >= total:
            raise RuntimeError('请求超出末页，官网可能返回了末页重复数据')
        if len(rows) > max(0, total - (page - 1) * size):
            raise RuntimeError('官网返回的分页记录数与总数矛盾')
    return {'source': url, **r}

def _page_params(page, size):
    if any((isinstance(v, bool) or not (isinstance(v, int) or (isinstance(v, str) and v.isascii() and v.isdigit())) for v in (page, size))):
        raise ValueError('页码和每页数量须为整数')
    return (int(page), int(size))

def dates(frequency='day'):
    if frequency not in ('day', 'week'):
        raise ValueError('frequency 必须为 day 或 week')
    return _get(('dayrankings' if frequency == 'day' else 'weekrankings') + '/datelist', {'pageSize': 10} if frequency == 'week' else None)

def rankings(period, frequency='day', page=1, size=30):
    """按官网日期列表返回的期次查询，保留原始收视率和榜单类型。"""
    page, size = _page_params(page, size)
    if frequency not in ('day', 'week') or page < 1 or (not 1 <= size <= 100):
        raise ValueError('频率、页码或每页数量无效')
    pat = '\\d{4}-\\d{2}-\\d{2}' if frequency == 'day' else '\\d{8}-\\d{8}'
    if not re.fullmatch(pat, str(period)):
        raise ValueError('日榜为 YYYY-MM-DD，周榜为 YYYYMMDD-YYYYMMDD')
    return _get(('dayrankings' if frequency == 'day' else 'weekrankings') + '/list', {'date': period, 'pageNum': page, 'pageSize': size})
