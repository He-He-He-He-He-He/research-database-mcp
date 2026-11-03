"""Clarivate Starter API 官方 UID 详情；凭据仅从钥匙串读取。"""
import release_runtime
import re
import subprocess
from urllib.parse import quote
import requests
URL = 'https://api.clarivate.com/apis/wos-starter/v1/documents/'
DOC = 'https://developer.clarivate.com/apis/wos-starter'

def detail(uid):
    if not isinstance(uid, str) or not re.fullmatch('[A-Z]{2,10}:[A-Za-z0-9_-]{1,80}', uid):
        raise ValueError('请输入 Starter 检索结果中的文献 UID')
    proc = release_runtime.run(['/usr/bin/security', 'find-generic-password', '-s', 'research-toolkit-wos-starter', '-a', 'zju-research-toolkit', '-w'], capture_output=True, text=True, timeout=20)
    if proc.returncode or not proc.stdout.strip():
        raise RuntimeError('钥匙串没有可用的 WOS Starter 密钥')
    try:
        response = requests.get(URL + quote(uid, safe=''), headers={'X-ApiKey': proc.stdout.strip()}, timeout=30)
    except requests.RequestException as error:
        raise RuntimeError('Clarivate 网络请求失败：' + type(error).__name__) from None
    if response.status_code != 200:
        raise RuntimeError('Clarivate 详情接口返回 HTTP ' + str(response.status_code))
    try:
        record = response.json()
    except ValueError:
        raise RuntimeError('Clarivate 返回非 JSON') from None
    if not isinstance(record, dict) or record.get('uid') != uid or (not record.get('title')):
        raise RuntimeError('返回记录 UID 或题名无法核对')
    return {'source': 'Clarivate Web of Science Starter API', 'documentation': DOC, 'uid': uid, 'record': record, 'note': '官方 UID 单条元数据及可用引文计数；不代表全文或学校网页版全部订阅，数据和第三方 AI 使用受适用协议限制。'}
