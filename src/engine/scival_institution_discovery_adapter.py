"""SciVal 官方机构分页发现与 ID 详情；不返回包含密钥的源链接。"""
import release_runtime
import re
from elsevier_scival_official_adapter import _fetch, _institution, DOC

def search(name, limit=10, page=0):
    if not isinstance(name, str) or not 1 <= len(name.strip()) <= 120 or re.search('[()\\x00-\\x1f]', name):
        raise ValueError('机构名称须为 1–120 字单行文本且不含括号')
    if type(limit) is not int or not 1 <= limit <= 50 or type(page) is not int or (not 0 <= page <= 100):
        raise ValueError('limit 须为 1–50，page 须为 0–100')
    raw, key = _fetch('search', {'query': 'name(' + name.strip() + ')', 'limit': limit, 'offset': page})
    if raw.get('results') is None:
        return {'source': 'Elsevier SciVal Institution API', 'documentation': DOC, 'returned_count': None, 'items': [], 'note': '结果列表缺失，不能判断是否无匹配。'}
    if not isinstance(raw['results'], list):
        raise RuntimeError('SciVal 机构结果格式异常')
    items = [_institution(x, key) for x in raw['results']]
    if len(items) > limit:
        raise RuntimeError('SciVal 返回数量超过请求页大小')
    return {'source': 'Elsevier SciVal Institution API', 'documentation': DOC, 'query': name.strip(), 'page': page, 'limit': limit, 'returned_count': len(items), 'items': items, 'note': '源站未给总数，页间排序可能变化；同名机构须核对国家和 SciVal ID，此 ID 不等于 Scopus Affiliation ID。'}

def lookup(institution_id):
    if not re.fullmatch('[1-9][0-9]{0,11}', str(institution_id)):
        raise ValueError('机构 ID 须为正整数')
    raw, key = _fetch(str(institution_id), {})
    item = _institution(raw.get('institution'), key)
    if str(item['id']) != str(institution_id):
        raise RuntimeError('SciVal 返回机构 ID 不一致')
    return {'source': 'Elsevier SciVal Institution API', 'documentation': DOC, 'institution': item, 'note': '按 SciVal ID 核对机构；名称与国家为源站原值，机构指标不能代表全部研究成果。'}
