"""CNCB-NGDC 内参基因数据库 ICG 官方公开 REST API。"""
import release_runtime
import re
import requests
BASE = 'https://ngdc.cncb.ac.cn/icg/api/json/'

def icg_lookup(kind, accession):
    if kind not in ('species', 'project', 'gene', 'publication'):
        raise ValueError('kind 必须为 species、project、gene 或 publication')
    if not isinstance(accession, str) or not re.fullmatch('[A-Za-z0-9._-]{1,100}', accession):
        raise ValueError('请输入记录编号')
    r = requests.get(BASE + kind + '/' + accession, timeout=20, allow_redirects=False)
    if r.status_code != 200:
        raise RuntimeError('上游 HTTP ' + str(r.status_code))
    data = r.json()
    if str(data.get('code')) != '200' or data.get('result') is None:
        raise ValueError('上游没有找到记录：' + str(data.get('message', '')))
    return data['result']
