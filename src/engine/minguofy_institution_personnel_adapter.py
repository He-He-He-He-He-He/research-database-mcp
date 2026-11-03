"""书同文民国风云历史人物任职检索，只返回站方字段。"""
import release_runtime
import re, requests
from bs4 import BeautifulSoup
BASE = 'https://gujiku.unihan.com.cn/'

def search(name='', organization='', post='', offset=0, limit=10):
    for value in (name, organization, post):
        if not isinstance(value, str) or len(value) > 100 or any((ord(c) < 32 or c in '$+' for c in value)):
            raise ValueError('检索词须为单行且不能包含 $ 或 +')
    if not any((v.strip() for v in (name, organization, post))):
        raise ValueError('姓名、机构、职务至少提供一项')
    if type(offset) is not int or not 0 <= offset <= 100000 or type(limit) is not int or (not 1 <= limit <= 30):
        raise ValueError('offset 或 limit 无效')
    name = name.strip()
    organization = organization.strip()
    post = post.strip()
    params = {'name': name, 'org': organization, 'post': post, 'start': offset, 'count': limit}
    try:
        with requests.Session() as s:
            r = s.get(BASE + 'Products/Search/QSL', timeout=20)
            r.raise_for_status()
            if not re.search('\\bzjdx\\b', BeautifulSoup(r.content, 'html.parser').get_text(' ', strip=True), re.I):
                raise RuntimeError('未确认书同文学校账户标记')
            r = s.get(BASE + 'minguofy/api/oldsearch/MinGuoSearchRW', params=params, timeout=20)
            r.raise_for_status()
            d = r.json()
    except requests.RequestException:
        raise RuntimeError('书同文请求失败') from None
    if not isinstance(d, dict) or d.get('searchStr') != name + '$' + organization + '$' + post or d.get('start') != offset or (type(d.get('total')) is not int) or (d['total'] < 0) or (type(d.get('count')) is not int) or (not isinstance(d.get('items'), list)) or (d['count'] != len(d['items'])) or (len(d['items']) > limit):
        raise RuntimeError('人物检索条件或分页异常')
    keys = ('name', 'organizationName', 'post', 'adTime', 'period', 'relegation', 'termOffice')
    items = []
    for x in d['items']:
        if not isinstance(x, dict) or not isinstance(x.get('name'), str):
            raise RuntimeError('人物条目异常')
        row = {}
        for k in keys:
            v = x.get(k)
            if v is not None and (not isinstance(v, str) or re.search('(?i)(?:https?://|(?:token|session|sid|apikey)\\s*=)', v)):
                raise RuntimeError('人物字段异常')
            row[k + '_raw'] = v
        items.append(row)
    return {'source': '书同文民国风云人物任职检索', 'account_marker': 'zjdx（书同文账户）', 'query': {'name': name, 'organization': organization, 'post': post}, 'offset': offset, 'limit': limit, 'total': d['total'], 'items': items, 'note': '站方回显检索条件与起始位置，字段保留原值及高亮 HTML；同名及多次任职可能重复，历史任职不是现任。书同文账户标记不证明此产品单独授权。'}
