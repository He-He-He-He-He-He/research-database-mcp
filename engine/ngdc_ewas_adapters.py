"""CNCB-NGDC EWAS Atlas 公共 REST API。"""
import release_runtime
import re
import requests
BASE = 'https://ngdc.cncb.ac.cn/ewas/rest/'

def _get(resource, params):
    r = requests.get(BASE + resource, params=params, timeout=20, allow_redirects=False)
    if r.status_code != 200:
        raise RuntimeError('上游 HTTP ' + str(r.status_code))
    data = r.json()
    if data.get('code') != 0:
        raise ValueError('EWAS 上游未返回成功: ' + str(data.get('msg', '')))
    return data['data']

def ewas_gene(gene_symbol):
    if not isinstance(gene_symbol, str) or not re.fullmatch('[A-Za-z0-9._-]{1,80}', gene_symbol):
        raise ValueError('请输入合法基因符号')
    return _get('gene', {'geneSymbol': gene_symbol})

def ewas_study(study_id):
    if not isinstance(study_id, str) or not re.fullmatch('ES\\d{5,12}', study_id):
        raise ValueError('请输入 EWAS 研究编号')
    return _get('study', {'studyId': study_id})

def ewas_probe(probe_id):
    if not isinstance(probe_id, str) or not re.fullmatch('[A-Za-z0-9_-]{2,80}', probe_id):
        raise ValueError('请输入探针编号')
    return _get('probe', {'probeId': probe_id})
