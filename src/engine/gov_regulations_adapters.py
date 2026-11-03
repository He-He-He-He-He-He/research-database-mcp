"""中国政府网国家规章库公开检索。"""
import release_runtime
import base64
import json
import subprocess
from urllib.parse import quote
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import padding
KEY = 'MIGfMA0GCSqGSIb3DQEBAQUAA4GNADCBiQKBgQCWGTHvPbNkzQNxTJwSZbsgHKyLl/OK11kCZNmVVSFK3lUbmHgh7Ain1gdaf7G/ETh/wQm/9BAO/U36yWPizzlwHCUcWJXBRsY10PsnYIlBXH/cjqQaEbmEghxcjdYtLtkudoMfoMDiJk+tPC7UEZd8TI2u26vttNF++6tHi1HdeQIDAQAB'
URL = 'https://sousuoht.www.gov.cn/athena/forward/16BEFE295A368744B016A3B58F2EA7F3CF8A5946EE6CFB7EE98938A538353125'

def search(keyword, page=1, mode='title'):
    """现行规章标题或正文检索，逐页读取官方原始结果。"""
    if isinstance(page, bool) or not (isinstance(page, int) or (isinstance(page, str) and page.isascii() and page.isdigit())):
        raise ValueError('页码须为整数')
    page = int(page)
    if not isinstance(keyword, str) or not keyword.strip() or page < 1 or (mode not in ('title', 'full')):
        raise ValueError('需提供关键词、正页码和 title/full 检索模式')
    token = serialization.load_der_public_key(base64.b64decode(KEY)).encrypt(b'f8f49ea85885466598c5261f7f8607fb', padding.PKCS1v15())
    encoded = quote(base64.b64encode(token).decode(), safe="~()*!.'-")
    kind = 'title' if mode == 'title' else 'all'
    payload = {'code': '18258ab0ac9', 'dataTypeId': '92', 'orderBy': 'time', 'customFilter': {'operator': 'or', 'properties': [{'property': 'f_202321360426', 'operator': 'eq', 'value': keyword if kind == 'title' else ''}, {'property': 'f_202321758948', 'operator': 'eq', 'value': keyword if kind == 'all' else ''}]}, 'searchBy': kind, 'trackTotalHits': 'true', 'granularity': 'ALL', 'isSearchForced': 0, 'filters': [], 'pageNo': page, 'pageSize': '7', 'minimumShouldMatch': '100%', 'searchType': 'TERM', 'slop': 5}
    p = release_runtime.run(['curl', '--fail', '--silent', '--show-error', '--max-time', '30', URL, '-H', 'Content-Type: application/json;charset=utf-8', '-H', 'athenaAppKey: ' + encoded, '-H', 'athenaAppName: ' + quote('规章库'), '-H', 'Origin: https://www.gov.cn', '--data', json.dumps(payload, ensure_ascii=False)], capture_output=True, text=True, timeout=35)
    if p.returncode:
        raise RuntimeError('国家规章库请求失败: ' + p.stderr.strip())
    try:
        response = json.loads(p.stdout)
        data = response['result']['data']
        pager = data['pager']
        records = data['middle']['list']
    except (ValueError, TypeError, KeyError) as exc:
        raise RuntimeError('国家规章库返回异常或接口结构变化') from exc
    if not isinstance(pager, dict) or not isinstance(records, list) or any((type(pager.get(k)) is not int for k in ('total', 'pageNo', 'pageSize', 'pageCount'))):
        raise RuntimeError('国家规章库分页结构异常')
    total = pager['total']
    size = pager['pageSize']
    if total < 0 or size != 7 or pager['pageNo'] != page or (pager['pageCount'] != (total + size - 1) // size) or (len(records) > min(size, max(0, total - (page - 1) * size))):
        raise RuntimeError('国家规章库分页结果矛盾')
    return {'source': 'https://www.gov.cn/zhengce/xxgk/gjgzk/index.htm', 'pager': pager, 'results': records}
