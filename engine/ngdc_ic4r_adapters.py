"""国家基因组科学数据中心 IC4R 水稻基因注释 API。"""
import release_runtime
import re
import requests
BASE = 'https://ngdc.cncb.ac.cn/ic4r/api/json/'

def _get(kind, locus):
    if not isinstance(locus, str) or not re.fullmatch('IC4R-[A-Za-z0-9_-]{1,80}', locus):
        raise ValueError('请输入 IC4R 基因位点编号')
    r = requests.get(BASE + kind + '/' + locus, timeout=20, allow_redirects=False)
    if r.status_code != 200:
        raise RuntimeError('上游 HTTP ' + str(r.status_code))
    data = r.json()
    if data is None:
        raise ValueError('未找到记录')
    return data

def ic4r_gene(locus):
    return _get('gene', locus)

def ic4r_functional_annotations(locus):
    return _get('annotation', locus)
