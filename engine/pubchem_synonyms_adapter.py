"""PubChem PUG-REST synonym/identifier list for one verified compound CID."""
import release_runtime
import re
import requests
BASE = 'https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/cid'

def synonyms(cid, limit=20, session=None, *, offset=0):
    cid = str(cid)
    if not re.fullmatch('[1-9]\\d{0,11}', cid):
        raise ValueError('PubChem CID 必须为正整数')
    if type(limit) is not int or not 1 <= limit <= 100:
        raise ValueError('返回数量须为 1–100')
    if type(offset) is not int or not 0 <= offset <= 1000000:
        raise ValueError('offset 须为 0–1000000')
    url = f'{BASE}/{cid}/synonyms/JSON'
    r = (session or requests).get(url, headers={'Accept': 'application/json', 'User-Agent': 'PersonalResearchToolkit/1.0'}, timeout=25)
    r.raise_for_status()
    d = r.json()
    items = d.get('InformationList', {}).get('Information') if isinstance(d, dict) else None
    if not isinstance(items, list) or len(items) != 1 or str(items[0].get('CID')) != cid or (not isinstance(items[0].get('Synonym'), list)) or (not all((isinstance(x, str) for x in items[0]['Synonym']))):
        raise ValueError('PubChem 同义名响应异常')
    names = items[0]['Synonym']
    return {'source': 'NCBI PubChem PUG-REST', 'source_url': url, 'documentation': 'https://pubchem.ncbi.nlm.nih.gov/docs/pug-rest', 'cid': int(cid), 'offset': offset, 'returned_count': len(names[offset:offset + limit]), 'upstream_count': len(names), 'next_offset': offset + limit if offset + limit < len(names) else None, 'synonyms': names[offset:offset + limit], 'note': '上游列表混合名称、登记号和其他标识；不代表每个名称均经权威核验，也不是 CAS 登记库或 SciFinder。按源端顺序在完整响应中截取；源端顺序可能变动，跨次请求不保证无遗漏。请核对具体化学结构和标识。'}
