"""PubChem compound-to-patent publication cross-references, not patent search."""
import release_runtime
import re
import requests
BASE = 'https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/cid'

def patents(cid, limit=10, session=None):
    cid = str(cid)
    if not re.fullmatch('[1-9]\\d{0,11}', cid):
        raise ValueError('PubChem CID 必须为正整数')
    if type(limit) is not int or not 1 <= limit <= 50:
        raise ValueError('返回数量须为 1–50')
    url = f'{BASE}/{cid}/xrefs/PatentID/JSON'
    r = (session or requests).get(url, headers={'Accept': 'application/json', 'User-Agent': 'PersonalResearchToolkit/1.0'}, timeout=35)
    r.raise_for_status()
    if len(r.content) > 12000000:
        raise ValueError('PubChem 响应超过 12MB，请缩小范围或稍后查询')
    d = r.json()
    items = d.get('InformationList', {}).get('Information') if isinstance(d, dict) else None
    if not isinstance(items, list) or len(items) != 1 or str(items[0].get('CID')) != cid or (not isinstance(items[0].get('PatentID'), list)) or (not all((isinstance(x, str) for x in items[0]['PatentID']))):
        raise ValueError('PubChem 专利交叉引用响应异常')
    ids = items[0]['PatentID']
    return {'source': 'NCBI PubChem PUG-REST compound patent cross-references', 'source_url': url, 'documentation': 'https://pubchem.ncbi.nlm.nih.gov/docs/pug-rest', 'cid': int(cid), 'upstream_count': len(ids), 'returned_count': min(limit, len(ids)), 'patent_publication_ids': ids[:limit], 'note': '仅为 PubChem 将化合物关联至专利公开号的交叉引用，不是专利全库或顾如检索；不代表权利要求涵盖该化合物、专利有效或法律状态。结果按上游顺序截取；每次 API 均传输完整关联列表，已实测跨请求结果顺序及前列集合会变化，不能将不同请求的片段拼接为完整列表。'}
