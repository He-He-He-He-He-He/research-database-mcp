"""ZBW EconBiz 经济与商业研究公开题录检索。"""
import release_runtime
import re
import requests
BASE = 'https://api.econbiz.de/v1'
FIELDS = ('id', 'title', 'creator', 'contributor', 'date', 'publisher', 'subject', 'source', 'type', 'type_genre', 'isPartOf', 'accessRights')

def _get(path, params=None):
    r = requests.get(BASE + path, params=params, timeout=25)
    r.raise_for_status()
    d = r.json()
    if d.get('status') != 200:
        raise ValueError('EconBiz 返回非成功状态')
    return d

def _item(x):
    if not re.fullmatch('\\d+', str(x.get('id', ''))) or not x.get('title'):
        raise ValueError('题录缺少编号或标题')
    return {k: x.get(k) for k in FIELDS}

def econbiz_search(query, page=1, page_size=10):
    if not isinstance(query, str) or not query.strip() or len(query) > 200:
        raise ValueError('关键词须为1–200字')
    if not isinstance(page, int) or isinstance(page, bool) or (not isinstance(page_size, int)) or isinstance(page_size, bool) or (page < 1) or (not 1 <= page_size <= 50):
        raise ValueError('页码须大于零，每页1–50条')
    d = _get('/search', {'q': query.strip(), 'size': page_size, 'from': (page - 1) * page_size + 1}).get('hits', {})
    if not isinstance(d.get('total'), int) or not isinstance(d.get('hits'), list):
        raise ValueError('EconBiz 返回结构不完整')
    return {'source': 'ZBW EconBiz 官方公共 API', 'query': query.strip(), 'total': d['total'], 'page': page, 'items': [_item(x) for x in d['hits']], 'note': '经济与商业跨源题录，不表示浙大机构订购或逐篇全文权限。'}

def econbiz_detail(record_id):
    rid = str(record_id)
    if not re.fullmatch('\\d+', rid):
        raise ValueError('编号须为数字')
    d = _get('/record/' + rid).get('record', {})
    if d.get('id') != rid:
        raise ValueError('详情编号不一致')
    return {'source': 'ZBW EconBiz 官方公共 API', 'item': _item(d), 'note': '题录元数据；访问标记不保证逐篇全文权限。'}
