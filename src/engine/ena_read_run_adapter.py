"""EMBL-EBI ENA public read-run metadata, not sequencing file downloads."""
import release_runtime
import re
import requests
from urllib.parse import urlencode
BASE = 'https://www.ebi.ac.uk/ena/portal/api/search'
FIELDS = 'run_accession,study_accession,study_title,scientific_name,first_public,last_updated'
HEADERS = {'Accept': 'application/json', 'User-Agent': 'PersonalResearchToolkit/1.0'}

def _fetch(query, limit, session):
    p = {'result': 'read_run', 'query': query, 'format': 'json', 'limit': limit, 'fields': FIELDS}
    r = (session or requests).get(BASE, params=p, headers=HEADERS, timeout=25)
    r.raise_for_status()
    d = r.json()
    if not isinstance(d, list) or any((not isinstance(x, dict) for x in d)):
        raise ValueError('ENA 响应格式异常')
    return {'source': 'EMBL-EBI European Nucleotide Archive, read_run', 'source_url': BASE + '?' + urlencode(p), 'documentation': 'https://ena-docs.readthedocs.io/en/latest/retrieval/programmatic-access/advanced-search.html', 'note': '每行是一个测序 run，多个 run 可属于同一研究项目；返回数量不是匹配总量，也不代表参与者数量。只返回公开元数据，不下载序列。', 'returned_rows': len(d), 'items': d}

def search(title, limit=5, session=None):
    if not isinstance(title, str) or not title.strip() or len(title) > 100 or any((c in title for c in '\\"*\r\n')):
        raise ValueError('研究标题词无效')
    if type(limit) is not int or not 1 <= limit <= 20:
        raise ValueError('单次返回限制为 1–20 条')
    return _fetch('study_title="*' + title.strip() + '*"', limit, session)

def run(accession, session=None):
    if not isinstance(accession, str) or not re.fullmatch('(?:DRR|ERR|SRR)\\d{6,12}', accession):
        raise ValueError('run 编号格式无效')
    data = _fetch('run_accession="' + accession + '"', 2, session)
    if len(data['items']) != 1 or data['items'][0].get('run_accession') != accession:
        raise ValueError('未找到唯一对应的公开 run')
    return data
