"""PubChem compound bioassay references and assay descriptions."""
import release_runtime
import re
import requests
BASE = 'https://pubchem.ncbi.nlm.nih.gov/rest/pug'
HEADERS = {'Accept': 'application/json', 'User-Agent': 'PersonalResearchToolkit/1.0'}
NOTE = 'PubChem 的 active 是其生物测定结果分类，受实验设计与数据来源限制，不代表临床有效、安全或获批；本接口不是 SciFinder，也不是医疗决策依据。'

def _positive(v, label):
    s = str(v)
    if not re.fullmatch('[1-9]\\d{0,11}', s):
        raise ValueError(label + '须为正整数')
    return s

def _get(url, params, session):
    r = (session or requests).get(url, params=params, headers=HEADERS, timeout=30)
    r.raise_for_status()
    if len(r.content) > 8000000:
        raise ValueError('上游响应超出大小限制')
    return r.json()

def active_assays(cid, limit=10, session=None, *, offset=0):
    cid = _positive(cid, 'CID')
    if type(limit) is not int or not 1 <= limit <= 50 or type(offset) is not int or (not 0 <= offset <= 1000000):
        raise ValueError('返回数量须为 1–50，offset 须为 0–1000000')
    url = f'{BASE}/compound/cid/{cid}/aids/JSON'
    d = _get(url, {'aids_type': 'active'}, session)
    x = d.get('InformationList', {}).get('Information') if isinstance(d, dict) else None
    if not isinstance(x, list) or len(x) != 1 or str(x[0].get('CID')) != cid or (not isinstance(x[0].get('AID'), list)) or (not all((type(n) is int for n in x[0]['AID']))):
        raise ValueError('PubChem 关联测定响应异常')
    aids = x[0]['AID']
    return {'source': 'NCBI PubChem PUG-REST', 'source_url': url + '?aids_type=active', 'cid': int(cid), 'upstream_count': len(aids), 'offset': offset, 'returned_count': len(aids[offset:offset + limit]), 'next_offset': offset + limit if offset + limit < len(aids) else None, 'assay_ids': aids[offset:offset + limit], 'note': NOTE + ' 上游每次返回完整列表，本地截取，不表示排名；跨次请求顺序可能变化。'}

def assay(aid, session=None):
    aid = _positive(aid, 'AID')
    url = f'{BASE}/assay/aid/{aid}/description/JSON'
    d = _get(url, None, session)
    cs = d.get('PC_AssayContainer') if isinstance(d, dict) else None
    if not isinstance(cs, list) or len(cs) != 1:
        raise ValueError('PubChem 生物测定详情异常')
    x = cs[0].get('assay', {}).get('descr', {})
    if str(x.get('aid', {}).get('id')) != aid:
        raise ValueError('测定 AID 不匹配')
    return {'source': 'NCBI PubChem PUG-REST', 'source_url': url, 'note': NOTE, 'description': x}
