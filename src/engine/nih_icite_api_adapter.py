"""NIH iCite official bibliometrics by PubMed identifier."""
import release_runtime
import requests
BASE = 'https://icite.od.nih.gov/api/pubs'

def lookup(pmids):
    if isinstance(pmids, str):
        ids = pmids.split(',')
    else:
        ids = list(pmids)
    ids = [str(x).strip() for x in ids]
    if not 1 <= len(ids) <= 200 or any((not x.isdigit() or int(x) < 1 for x in ids)):
        raise ValueError('请输入 1–200 个有效 PMID')
    r = requests.get(BASE, params={'pmids': ','.join(ids)}, timeout=30)
    r.raise_for_status()
    j = r.json()
    if not isinstance(j.get('data'), list):
        raise RuntimeError('服务未返回题录列表')
    found = {str(x.get('pmid')) for x in j['data']}
    return {'requested': ids, 'not_returned': [x for x in ids if x not in found], 'data': j['data'], 'source': 'NIH iCite / Open Citation Collection', 'note': '未返回或缺失的指标不等于零；引用覆盖范围不等同所有数据库。'}

def list_publications(year=None, offset=None, limit=10):
    if not 1 <= int(limit) <= 200:
        raise ValueError('limit 为 1–200')
    params = {'limit': int(limit)}
    if year is not None:
        if not 1800 <= int(year) <= 2100:
            raise ValueError('年份无效')
        params['year'] = int(year)
    if offset is not None:
        if int(offset) < 0:
            raise ValueError('offset 不能为负')
        params['offset'] = int(offset)
    r = requests.get(BASE, params=params, timeout=30)
    r.raise_for_status()
    j = r.json()
    if not isinstance(j.get('data'), list):
        raise RuntimeError('服务未返回题录列表')
    return {'source': 'NIH iCite', 'query': params, 'response': j, 'note': 'offset 是 PMID 下界，不是常规跳过条数。'}
