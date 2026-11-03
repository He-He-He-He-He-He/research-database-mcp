"""SciVal 官方国家/地区名称发现与代码核验，不返回带密钥的链接。"""
import release_runtime
import re
from elsevier_scival_official_adapter import _fetch, _text, COUNTRY_BASE, COUNTRY_DOC

def _country(item, key):
    if not isinstance(item, dict) or type(item.get('id')) is not int or item['id'] < 1:
        raise RuntimeError('SciVal 国家或地区 ID 异常')
    code = _text(item.get('countryCode'), key)
    if not re.fullmatch('[A-Z]{3}', code):
        raise RuntimeError('SciVal 国家或地区代码异常')
    return {'id': item['id'], 'name': _text(item.get('name'), key), 'countryCode': code}

def search(name, limit=10, page=0):
    if not isinstance(name, str) or not 1 <= len(name.strip()) <= 120 or re.search('[()\\x00-\\x1f]', name):
        raise ValueError('名称须为 1–120 字单行文本且不含括号')
    if type(limit) is not int or not 1 <= limit <= 20 or type(page) is not int or (not 0 <= page <= 100):
        raise ValueError('limit 须为 1–20，page 须为 0–100')
    raw, key = _fetch('search', {'query': 'name(' + name.strip() + ')', 'limit': limit, 'offset': page}, COUNTRY_BASE)
    if 'results' not in raw or raw['results'] is None:
        return {'source': 'Elsevier SciVal Country API', 'documentation': COUNTRY_DOC, 'items': [], 'returned_count': None, 'note': '响应缺少结果列表，不能判断是否无匹配。'}
    if not isinstance(raw['results'], list):
        raise RuntimeError('SciVal 国家或地区结果列表异常')
    items = [_country(x, key) for x in raw['results']]
    if len(items) > limit:
        raise RuntimeError('SciVal 返回数量超过请求页大小，不能确认分页')
    return {'source': 'Elsevier SciVal Country API', 'documentation': COUNTRY_DOC, 'query': name.strip(), 'page': page, 'limit': limit, 'returned_count': len(items), 'items': items, 'note': '名称及代码来自 SciVal；文档将 offset 描述为跳过的页数，未提供总数，结果可能随源站更新。请核对代码后再查指标。'}

def lookup(code):
    if not isinstance(code, str) or not re.fullmatch('[A-Za-z]{3}', code):
        raise ValueError('代码须为 3 个英文字母')
    code = code.upper()
    raw, key = _fetch('code/' + code, {}, COUNTRY_BASE)
    item = _country(raw.get('country'), key)
    if item['countryCode'] != code:
        raise RuntimeError('SciVal 返回代码与请求不一致')
    return {'source': 'Elsevier SciVal Country API', 'documentation': COUNTRY_DOC, 'country': item, 'note': '国家或地区名称及代码按 SciVal 返回；可使用代码查询已有国家指标。'}
