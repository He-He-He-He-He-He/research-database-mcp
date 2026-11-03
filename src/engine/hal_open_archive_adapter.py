"""HAL open archive metadata via the official CCSD search API."""
import release_runtime
import re
from urllib.parse import urlencode
import requests
BASE = 'https://api.archives-ouvertes.fr/search/'
FIELDS = 'docid,halId_s,title_s,authFullName_s,producedDate_s,doiId_s,docType_s,uri_s'
HEADERS = {'Accept': 'application/json', 'User-Agent': 'PersonalResearchToolkit/1.0'}

def _query(q, size, offset, session):
    params = {'q': q, 'rows': size, 'start': offset, 'wt': 'json', 'fl': FIELDS}
    r = (session or requests).get(BASE, params=params, headers=HEADERS, timeout=25)
    r.raise_for_status()
    j = r.json()
    d = j.get('response') if isinstance(j, dict) else None
    if not isinstance(d, dict) or not isinstance(d.get('docs'), list) or (not isinstance(d.get('numFound'), int)):
        raise ValueError('HAL API 返回格式异常')
    return {'source': 'HAL open archive / CCSD', 'source_url': BASE + '?' + urlencode(params), 'documentation': 'https://api.archives-ouvertes.fr/docs/search', 'note': '仅 HAL 题录，包含 NOTICE 类型的不等于存在可获取全文。HAL 关于元数据 CC0 与抽取数据商业使用的官方说明存在冲突；仅按个人研究使用，商业和第三方服务处理权限请先核实。', 'data': d}

def search_title(title, size=5, offset=0, session=None):
    if not isinstance(title, str) or not title.strip() or len(title) > 200:
        raise ValueError('题名不能为空且最多 200 字符')
    if type(size) is not int or not 1 <= size <= 20 or type(offset) is not int or (not 0 <= offset <= 10000):
        raise ValueError('分页参数无效')
    term = title.strip().replace('\\', '\\\\').replace('"', '\\"')
    return _query('title_t:"' + term + '"', size, offset, session)

def detail(hal_id, session=None):
    if not isinstance(hal_id, str) or not re.fullmatch('hal-\\d{8}', hal_id):
        raise ValueError('HAL 编号格式应为 hal- 加 8 位数字')
    x = _query('halId_s:"' + hal_id + '"', 5, 0, session)
    if x['data']['numFound'] < 1 or not all((r.get('halId_s') == hal_id for r in x['data']['docs'])):
        raise ValueError('HAL 编号不存在或返回结果不匹配')
    return x
