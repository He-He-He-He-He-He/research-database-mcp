"""国家基因组科学数据中心 Genome Warehouse 公开元数据。"""
import release_runtime
import re
import requests
BASE = 'https://ngdc.cncb.ac.cn/gwh/api/public/'
PATTERNS = {'genome': '\\d{1,12}', 'assembly': 'GWH[A-Za-z0-9]{8,40}', 'bioProject': 'PRJ[A-Za-z0-9]{3,40}', 'bioSample': 'SAM[A-Za-z0-9]{3,40}'}

def gwh_lookup(kind, identifier):
    if kind not in PATTERNS or not isinstance(identifier, str) or (not re.fullmatch(PATTERNS[kind], identifier)):
        raise ValueError('请检查记录类型与编号')
    r = requests.get(BASE + kind + '/' + identifier, timeout=20, allow_redirects=False)
    if r.status_code != 200:
        raise RuntimeError('上游 HTTP ' + str(r.status_code))
    x = r.json()
    if not isinstance(x, dict) or not x or x.get('message') not in (None, 'SUCCESS'):
        raise ValueError('上游未找到记录')
    return x
