"""HBN institution IP login and indicator catalog, no bulk data download."""
import release_runtime
import re
from urllib.parse import urljoin
import requests
from bs4 import BeautifulSoup
BASE = 'https://data.harborn.cn/'

def _headers(s):
    r = s.get(BASE, timeout=20)
    r.raise_for_status()
    p = BeautifulSoup(r.content, 'html.parser')
    src = next((x.get('src') for x in p.select('script[src]') if re.fullmatch('/js/app\\.[a-f0-9]+\\.js', x.get('src', ''))), None)
    if not src:
        raise RuntimeError('站方前端配置缺失')
    r = s.get(urljoin(BASE, src), timeout=20)
    r.raise_for_status()
    m = re.search('url:"/auth/oauth/token",headers:\\{isToken:!1,Authorization:"(Basic [A-Za-z0-9+/=]+)"', r.text)
    if not m:
        raise RuntimeError('站方 IP 登录配置变化')
    r = s.get(BASE + 'auth/token/ip', timeout=20)
    r.raise_for_status()
    j = r.json()
    ip = j.get('data') if isinstance(j, dict) else None
    if not isinstance(ip, str) or not re.fullmatch('\\d{1,3}(?:\\.\\d{1,3}){3}', ip):
        raise RuntimeError('站方未返回 IP')
    p = {'grant_type': 'password', 'scope': 'server', 'client': 2, 'ip': ip, 'iplogin': ip, 'loginFirst': 'true'}
    r = s.post(BASE + 'auth/oauth/token', params=p, headers={'Authorization': m.group(1)}, timeout=20)
    r.raise_for_status()
    j = r.json()
    token = j.get('access_token') if isinstance(j, dict) else None
    if not isinstance(token, str) or not token:
        raise RuntimeError('IP 登录未返回会话')
    headers = {'Authorization': 'Bearer ' + token}
    r = s.get(BASE + 'admin/user/info', params={'client': 2}, headers=headers, timeout=20)
    r.raise_for_status()
    j = r.json()
    d = j.get('data') if isinstance(j, dict) else None
    u = d.get('userLogin') if isinstance(d, dict) else None
    if not isinstance(j, dict) or j.get('code') != 0 or (not isinstance(u, dict)) or (u.get('userName') != '浙江大学') or (str(d.get('ipAllow')) != '1'):
        raise RuntimeError('未确认浙江大学 IP 机构身份')
    return headers

def search(keyword, page=1, limit=5, session=None, database=''):
    if not isinstance(keyword, str) or not 1 <= len(keyword.strip()) <= 100:
        raise ValueError('关键词须为 1–100 字')
    if not isinstance(page, int) or isinstance(page, bool) or page < 1:
        raise ValueError('页码须为正整数')
    if not isinstance(limit, int) or isinstance(limit, bool) or (not 1 <= limit <= 10):
        raise ValueError('每次最多 10 条')
    if not isinstance(database, str) or (database and (not re.fullmatch('[A-Za-z0-9_]{1,80}', database))):
        raise ValueError('数据库代码须为字母、数字或下划线')
    q = keyword.strip()
    s = session or requests.Session()
    headers = _headers(s)
    offset = (page - 1) * limit
    first = offset // 50
    skip = offset % 50

    def fetch(number):
        r = s.post(BASE + 'db/searchDb/esAllInfo', json={'name': q, 'type': '0', 'dbId': database, 'pageNo': number}, headers=headers, timeout=25)
        r.raise_for_status()
        j = r.json()
        d = j.get('data') if isinstance(j, dict) else None
        if not isinstance(j, dict) or j.get('code') != 0 or (not isinstance(d, dict)) or (d.get('pageNo') != number) or (type(d.get('total')) is not int) or (d['total'] < 0) or (not isinstance(d.get('results'), list)) or (len(d['results']) != min(50, max(0, d['total'] - number * 50))):
            raise RuntimeError('指标目录响应异常或分页不完整')
        return d
    d = fetch(first)
    results = d['results'][skip:skip + limit]
    if len(results) < limit and offset + len(results) < d['total']:
        nxt = fetch(first + 1)
        if nxt['total'] != d['total']:
            raise RuntimeError('指标目录翻页期间总数发生变化，请重试')
        results += nxt['results'][:limit - len(results)]
    keys = ('id', 'cn_name', 'en_name', 'type', 'startTime', 'endTime', 'unit', 'code', 'dbid', 'tree1id', 'tree1name', 'tree2id', 'tree2name', 'tree3id', 'tree3name', 'tree4id', 'tree4name', 'tree5id', 'tree5name', 'tree6id', 'tree6name', 'update_time')
    items = []
    for x in results:
        if not isinstance(x, dict) or not isinstance(x.get('id'), str) or (not isinstance(x.get('cn_name'), str)):
            raise RuntimeError('指标编号或名称缺失')
        if database and x.get('dbid') != database:
            raise RuntimeError('结果数据库代码与筛选不一致')
        items.append({k: x.get(k) for k in keys})
    result = {'source': 'HBN 环球财经数据库', 'institution': '浙江大学', 'query': q, 'page': page, 'total': d['total'], 'items': items, 'note': '按 limit 连续分页，翻页时须保持 limit 不变；旧版本页码对应位置不同。站方关键词可能广义匹配，单位和原始分类保留；不包含指标数值或逐项数据权限。'}
    if database:
        result['database_requested'] = database
        result['note'] += ' 已逐条核对返回子库代码；零结果不证明代码有效或该库无数据。'
    return result
