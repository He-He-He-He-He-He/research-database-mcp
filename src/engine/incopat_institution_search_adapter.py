"""incoPat 高校版网页题录检索；经校内 IP 登录，非厂商开放 API。"""
import release_runtime
import base64
import json
import re
import subprocess
from urllib.parse import urlparse
import requests
from bs4 import BeautifulSoup
BASE = 'https://www.incopat.com'
INFO = 'https://libdb.zju.edu.cn/s/lib/libtb/show/1874'
FIELDS = ('pn', 'pnc', 'an', 'san', 'ad', 'pd', 'ti_cn', 'ti_en', 'ti_otlang', 'tio', 'ab_cn', 'ab_en', 'ab_otlang', 'abo', 'pat', 'ap_gs', 'ap_or', 'in_or', 'ipc', 'ipcList', 'status', 'status_cn', 'status_lite', 'status_lite_cn')

def _decode(text):
    if not isinstance(text, str) or len(text) < 33 or len(text) > 12000000:
        raise RuntimeError('incoPat 检索响应格式异常')
    try:
        key = text[:16].encode('ascii')
        iv = text[16:32].encode('ascii')
        ciphertext = base64.b64decode(text[32:], validate=True)
        p = release_runtime.run(['openssl', 'enc', '-d', '-aes-128-cbc', '-K', key.hex(), '-iv', iv.hex()], input=ciphertext, capture_output=True, timeout=10)
        if p.returncode:
            raise ValueError('decrypt')
        obj = json.loads(p.stdout)
    except (ValueError, UnicodeError, subprocess.SubprocessError, OSError):
        raise RuntimeError('incoPat 网页响应解码失败，可能已改变格式') from None
    if not isinstance(obj, dict):
        raise RuntimeError('incoPat 检索响应结构异常')
    return obj

def search(query, page=1, limit=10, field='all'):
    if not isinstance(query, str) or not 1 <= len(query.strip()) <= 120 or re.search('[\\x00-\\x1f()=<>]', query):
        raise ValueError('检索词须为 1–120 字单行文本，不支持公式或括号')
    if field not in ('all', 'title', 'applicant', 'inventor', 'patent-number', 'ipc', 'abstract'):
        raise ValueError('不支持的检索字段')
    if field in ('title', 'applicant', 'inventor', 'abstract') and (not re.fullmatch('[\\w\\s-]+', query)):
        raise ValueError('指定字段查询仅支持文字、数字、空格和连字符')
    if field == 'patent-number' and (not re.fullmatch('[A-Za-z0-9]{4,40}', query)):
        raise ValueError('专利号码仅支持字母和数字')
    if field == 'ipc' and (not re.fullmatch('[A-Za-z][0-9]{2}[A-Za-z](?:[0-9]{1,4}/[0-9]{1,6})?', query)):
        raise ValueError('IPC 格式示例 G06F 或 G06F17/50')
    if type(page) is not int or not 1 <= page <= 50 or type(limit) is not int or (not 1 <= limit <= 20):
        raise ValueError('page 须为 1–50，limit 须为 1–20')
    query = query.strip()
    session = requests.Session()
    try:
        r = session.get(BASE + '/ip', params={'locale': 'zh_CN'}, timeout=20)
        r.raise_for_status()
        form = BeautifulSoup(r.text, 'html.parser').select_one('form#loginForm')
        if not form or form.get('action', '').lower() != '/dologin':
            raise RuntimeError('incoPat IP 登录页结构异常')
        values = {x.get('name'): x.get('value', '') for x in form.select('input[name]')}
        r = session.post(BASE + '/doLogin', data=values, timeout=20)
        r.raise_for_status()
        location = urlparse(r.url)
        if location.hostname != 'www.incopat.com' or location.path != '/home/schoolHome' or '浙江大学图书馆' not in BeautifulSoup(r.text, 'html.parser').get_text(' ', strip=True):
            raise RuntimeError('incoPat 未确认浙江大学图书馆 IP 登录')
        r = session.post(BASE + '/advancedSearch/simpleInit', data={'searchValue': query, 'zhcn': 'true', 'foreign': 'true'}, timeout=20)
        r.raise_for_status()
        form = BeautifulSoup(r.text, 'html.parser').select_one('#solrQueryBeanform')
        if not form:
            raise RuntimeError('incoPat 检索页面结构异常')
        data = {x.get('name'): x.get('value', '') for x in form.select('input[name]')}
        data.update(formerQuery={'all': 'ALL', 'title': 'TI', 'applicant': 'AP', 'inventor': 'IN', 'abstract': 'AB', 'patent-number': 'PN', 'ipc': 'IPC'}[field] + '=(' + query + ')', database='all', fields='PN,TI-CN,TI-EN,AB-CN,AB-EN,PD,AD,AP-OR,IN-OR,IPC', selectShow='graphic', page=str(page), rows=str(limit), accessLog='simpleSearch')
        r = session.post(BASE + '/solrResult/graphic', json=data, timeout=30)
        r.raise_for_status()
    except requests.RequestException as e:
        raise RuntimeError('incoPat 网络或服务请求失败：' + type(e).__name__) from None
    obj = _decode(r.text)
    d = obj.get('data')
    attrs = obj.get('attributeMap')
    if obj.get('status') is not True or obj.get('messages') or (not isinstance(d, dict)) or (not isinstance(attrs, dict)):
        raise RuntimeError('incoPat 检索未成功或响应结构异常')
    rows = d.get('content')
    number = d.get('number')
    total = d.get('totalElements')
    if not isinstance(rows, list) or len(rows) > limit or any((not isinstance(x, dict) or not x.get('pn') for x in rows)) or (type(number) is not int) or (number != page - 1) or (type(total) is not int) or (total < 0):
        raise RuntimeError('incoPat 返回页码或题录结构异常')
    expected = min(limit, max(0, total - (page - 1) * limit))
    if len(rows) != expected:
        raise RuntimeError('站方返回条数与总数及页码不一致，可能数据变化或响应不完整')
    result = {'source': 'incoPat 高校版机构网页检索', 'source_page': INFO, 'query': query, 'page': page, 'upstream_page_size': limit, 'total_raw': total, 'search_count_raw': attrs.get('searchCount'), 'items': [{k: x[k] for k in FIELDS if k in x} for x in rows[:limit]], 'note': '校内 IP 登录后使用厂商网页同源检索及其客户端响应格式；非官方开放 API。站方页大小由 limit 决定，连续翻页须保持一致；总数及翻译、法律状态均为源站原值，不代表法律意见、全文或下载授权；按总数和回显页号校验条数，数据可能变化。'}
    if field != 'all':
        result['field_requested'] = field
        result['note'] += ' 按站方所选字段请求，条件未由站方回显；可能分词或翻译匹配，逐条相关性须核对。'
        if field in ('applicant', 'inventor'):
            result['note'] += ' 相似名称或姓名可能匹配，不能据此认定机构或个人身份。'
        if field == 'abstract':
            result['note'] += ' 摘要为站方原值，不等同专利全文或下载授权。'
        if field in ('patent-number', 'ipc'):
            result['note'] += ' 专利号及 IPC 按原站值返回，匹配方式和分类版本须逐项核对。'
    return result
