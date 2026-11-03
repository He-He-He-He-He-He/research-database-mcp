"""国家基因组科学数据中心 RCoV19 公开序列元数据搜索。"""
import release_runtime
import re
import requests
BASE = 'https://ngdc.cncb.ac.cn/ncov/api/es/genome/query'

def coronavirus_genomes(keyword='', accession='', start=0, length=10):
    if not isinstance(keyword, str) or len(keyword) > 100 or (not isinstance(accession, str)) or (accession and (not re.fullmatch('[A-Za-z0-9_.-]{1,80}', accession))) or (not isinstance(start, int)) or (start < 0) or (not isinstance(length, int)) or (not 1 <= length <= 100):
        raise ValueError('检查关键词、序列号、起始位置及数量（1–100）')
    if not keyword and (not accession):
        raise ValueError('需要关键词或序列号')
    params = {'start': start, 'length': length}
    if keyword:
        params['q'] = keyword
    if accession:
        params['accession'] = accession
    r = requests.get(BASE, params=params, timeout=20, allow_redirects=False)
    if r.status_code != 200:
        raise RuntimeError('上游 HTTP ' + str(r.status_code))
    result = r.json().get('result')
    if not isinstance(result, dict) or not isinstance(result.get('data'), list):
        raise ValueError('上游未返回序列元数据')
    return result

def coronavirus_genome_detail(accession):
    rows = coronavirus_genomes(accession=accession, length=10)['data']
    for x in rows:
        if x.get('accession', '').lower() == accession.lower():
            return x
    raise ValueError('未找到精确序列号')
