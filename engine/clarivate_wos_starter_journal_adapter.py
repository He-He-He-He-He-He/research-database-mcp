"""Clarivate Starter 官方期刊 ISSN 查询。"""
import release_runtime
import re
import subprocess
import requests
URL = 'https://api.clarivate.com/apis/wos-starter/v1/journals'
DOC = 'https://developer.clarivate.com/apis/wos-starter'

def search(issn):
    if not isinstance(issn, str) or not re.fullmatch('\\d{4}-\\d{3}[\\dXx]', issn):
        raise ValueError('ISSN 须为 0000-0000 格式')
    issn = issn.upper()
    p = release_runtime.run(['/usr/bin/security', 'find-generic-password', '-s', 'research-toolkit-wos-starter', '-a', 'zju-research-toolkit', '-w'], capture_output=True, text=True, timeout=20)
    if p.returncode or not p.stdout.strip():
        raise RuntimeError('钥匙串没有可用的 WOS Starter 密钥')
    try:
        r = requests.get(URL, params={'issn': issn}, headers={'X-ApiKey': p.stdout.strip()}, timeout=30)
    except requests.RequestException as e:
        raise RuntimeError('Clarivate 网络请求失败：' + type(e).__name__) from None
    if r.status_code != 200:
        raise RuntimeError('Clarivate 期刊接口返回 HTTP ' + str(r.status_code))
    try:
        body = r.json()
    except ValueError:
        raise RuntimeError('Clarivate 返回非 JSON') from None
    if not isinstance(body, dict) or not isinstance(body.get('hits'), list) or (not isinstance(body.get('metadata'), dict)):
        raise RuntimeError('Clarivate 期刊响应结构异常')
    for item in body['hits']:
        if not isinstance(item, dict) or not item.get('id') or (not item.get('name')):
            raise RuntimeError('期刊记录缺少标识或名称')
    return {'source': 'Clarivate Web of Science Starter API 期刊', 'documentation': DOC, 'issn': issn, 'metadata': body['metadata'], 'items': body['hits'], 'note': '官方 ISSN 期刊匹配元数据及可用 JCR 链接，不返回影响因子或分区；不证明学校期刊全文权限。'}
