"""World Register of Marine Species (WoRMS) 全球海洋物种官方 API。"""
import release_runtime
from urllib.parse import quote
import requests
BASE = 'https://www.marinespecies.org/rest/'
OPERATIONS = {'record': 'AphiaRecordByAphiaID', 'classification': 'AphiaClassificationByAphiaID', 'distribution': 'AphiaDistributionsByAphiaID', 'synonyms': 'AphiaSynonymsByAphiaID', 'vernacular': 'AphiaVernacularsByAphiaID', 'sources': 'AphiaSourcesByAphiaID', 'children': 'AphiaChildrenByAphiaID'}

def _get(path, params=None):
    r = requests.get(BASE + path, params=params, timeout=30)
    r.raise_for_status()
    return {'source': 'World Register of Marine Species (WoRMS)', 'source_url': r.url, 'data': None if r.status_code == 204 else r.json(), 'note': '原始分类或分布记录，区分有效名与异名；分布记录不保证完整，也不等同实测出现记录。'}

def search(name, offset=1, like=False, marine_only=True):
    if not isinstance(name, str) or not 2 <= len(name.strip()) <= 150:
        raise ValueError('学名须为2–150字符')
    if isinstance(offset, bool) or not isinstance(offset, int) or (not 1 <= offset <= 100000):
        raise ValueError('offset无效')
    if not isinstance(like, bool) or not isinstance(marine_only, bool):
        raise ValueError('筛选参数须为布尔值')
    return _get('AphiaRecordsByName/' + quote(name.strip(), safe=''), {'offset': offset, 'like': str(like).lower(), 'marine_only': str(marine_only).lower()})

def details(aphia_id, kind='record', offset=1):
    if isinstance(aphia_id, bool) or not isinstance(aphia_id, int) or aphia_id < 1:
        raise ValueError('AphiaID须为正整数')
    if kind not in OPERATIONS:
        raise ValueError('未知资料类型')
    if isinstance(offset, bool) or not isinstance(offset, int) or offset < 1:
        raise ValueError('offset无效')
    return _get(OPERATIONS[kind] + '/' + str(aphia_id), {'offset': offset} if kind == 'children' else None)
