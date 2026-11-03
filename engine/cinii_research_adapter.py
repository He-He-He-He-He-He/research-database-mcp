"""CiNii Research official OpenSearch v1 using a Keychain application ID."""
import release_runtime
import json
import subprocess
from urllib.parse import urlencode
SERVICE = 'research-toolkit-cinii'

def _key():
    from imap_otp_mcp.server import config
    account, _, _ = config()
    p = release_runtime.run(['/usr/bin/security', 'find-generic-password', '-s', SERVICE, '-a', account, '-w'], capture_output=True, text=True, timeout=15)
    if p.returncode or not p.stdout.strip():
        raise RuntimeError('无法读取 CiNii 应用编号')
    return p.stdout.strip()

def search(keyword, kind='all', count=10, start=1):
    if not isinstance(keyword, str) or not keyword.strip() or len(keyword) > 100 or any((ord(c) < 32 for c in keyword)):
        raise ValueError('关键词须为1–100字单行文本')
    if kind not in ('all', 'articles', 'books', 'data', 'dissertations', 'projects'):
        raise ValueError('未知检索类型')
    if type(count) is not int or not 1 <= count <= 50 or type(start) is not int or (not 1 <= start <= 100000):
        raise ValueError('count或start超出范围')
    key = _key()
    if len(key) > 500 or any((c in key for c in '\r\n"\\')):
        raise RuntimeError('CiNii 应用编号格式无效')
    url = 'https://cir.nii.ac.jp/opensearch/' + kind + '?' + urlencode({'q': keyword.strip(), 'count': count, 'start': start, 'format': 'json', 'appid': key})
    try:
        p = release_runtime.run(['/usr/bin/curl', '--silent', '--show-error', '--proto', '=https', '--max-time', '35', '--max-filesize', '16000000', '--config', '-', '--write-out', '\n__STATUS__%{http_code}'], input='url = "' + url + '"\n', capture_output=True, text=True, timeout=40)
    except (OSError, subprocess.TimeoutExpired):
        raise RuntimeError('CiNii 网络请求失败') from None
    raw, sep, status = p.stdout.rpartition('\n__STATUS__')
    if p.returncode or not sep:
        raise RuntimeError('CiNii 网络请求失败')
    if status != '200':
        raise RuntimeError('CiNii 返回 HTTP ' + status[:3])
    if len(raw.encode('utf-8')) > 16000000:
        raise RuntimeError('CiNii 响应超过16MB')
    try:
        j = json.loads(raw)
    except ValueError:
        raise RuntimeError('CiNii 未返回有效 JSON') from None
    if not isinstance(j, dict) or not isinstance(j.get('items'), list):
        raise RuntimeError('CiNii 响应结构异常')

    def scrub(v):
        if isinstance(v, str):
            return v.replace(key, '[redacted]')
        if isinstance(v, list):
            return [scrub(x) for x in v]
        if isinstance(v, dict):
            return {k: scrub(x) for k, x in v.items() if str(k).lower() != 'appid'}
        return v
    return {'source': 'CiNii Research OpenSearch', 'query': keyword.strip(), 'kind': kind, 'requested_start': start, 'requested_count': count, 'total': j.get('opensearch:totalResults'), 'start': j.get('opensearch:startIndex'), 'per_page': j.get('opensearch:itemsPerPage'), 'items': scrub(j['items']), 'note': '源站题录与摘要可能混合不同类型，分页可能随索引更新变化；开放标识不等于全文或机构授权。'}
