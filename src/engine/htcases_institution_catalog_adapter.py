"""HTCases institution IP case-metadata catalog, no content downloads."""
import release_runtime
import hashlib
import re
import secrets
from urllib.parse import urljoin, urlparse
import requests
from bs4 import BeautifulSoup
FRONT = 'https://www.htcases.com.cn/v/'
API = 'https://www.htcases.com/front/'

def _config(s):
    r = s.get(FRONT, timeout=20)
    r.raise_for_status()
    p = BeautifulSoup(r.content, 'html.parser')
    src = next((x.get('src') for x in p.select('script[src]') if re.fullmatch('/v/static/js/app\\.[a-f0-9]+\\.js', x.get('src', ''))), None)
    if not src:
        raise RuntimeError('原站前端配置缺失')
    r = s.get(urljoin(FRONT, src), timeout=20)
    r.raise_for_status()
    text = r.text
    m = re.search('appId:"(\\d+)",nonce_str:.*?i=Object\\([A-Za-z_$][\\w$]*\\.a\\)\\(i,"([A-Za-z0-9]+)"\\)', text, re.S)
    if not m:
        raise RuntimeError('原站请求配置改变')
    return (m.group(1), m.group(2))

def _post(s, path, params, config):
    app, key = config
    d = {'appId': app, 'nonce_str': secrets.token_hex(8), **params}
    raw = ''.join((f'{k}={v}&' for k, v in sorted(d.items()) if v is not None and v != '' and (not isinstance(v, (list, dict))))) + 'key=' + key
    d['sign'] = hashlib.md5(raw.encode()).hexdigest().upper()
    r = s.post(API + path, data=d, timeout=25)
    r.raise_for_status()
    j = r.json()
    if not isinstance(j, dict) or j.get('status') is not True or str(j.get('code')) != '200':
        raise RuntimeError('原站请求失败')
    return j

def _require_institution(session,config):
    identity=_post(session,'client/org/getByIp',{},config).get('body')
    if not isinstance(identity,dict) or identity.get('name')!='浙江大学':
        raise RuntimeError('未确认本次会话的浙江大学 IP 机构身份；目录与详情均要求 getByIp 名称精确匹配')
    return identity

def search(keyword, page=1, limit=5, session=None):
    if not isinstance(keyword, str) or not 1 <= len(keyword.strip()) <= 100:
        raise ValueError('关键词须为 1–100 字')
    if not isinstance(page, int) or isinstance(page, bool) or page < 1:
        raise ValueError('页码须为正整数')
    if not isinstance(limit, int) or isinstance(limit, bool) or (not 1 <= limit <= 10):
        raise ValueError('每页最多 10 条')
    q = keyword.strip()
    s = session or requests.Session()
    config = _config(s)
    _require_institution(s,config)
    j = _post(s, 'lib/metadata/query', {'queryTxt': q, 'pageNo': page, 'pageSize': limit}, config)
    total = j.get('totalCount')
    rows = j.get('body')
    if type(total) is not int or total < 0 or (not isinstance(rows, list)) or (len(rows) > limit):
        raise RuntimeError('案例目录响应异常')
    expected = min(limit, max(0, total - (page - 1) * limit))
    if len(rows) != expected:
        raise RuntimeError('站方返回条数与总数及页码不一致，可能超出范围返回其他页、数据变化或响应不完整')
    items = []
    for x in rows:
        if not isinstance(x, dict) or type(x.get('id')) is not int or (not isinstance(x.get('title'), str)):
            raise RuntimeError('案例编号或标题缺失')
        items.append({'id': x['id'], 'title': x['title'], 'author': x.get('author'), 'source': x.get('source'), 'publication_date_raw': x.get('publicationDate'), 'case_library': x.get('caseLibName'), 'case_library_type': x.get('caseLibType'), 'language': x.get('language')})
    return {'source': '全球案例发现系统', 'institution': '浙江大学', 'query': q, 'page': page, 'page_size': limit, 'total': total, 'items': items[:limit], 'note': 'IP 机构下案例素材元数据检索，不代表每项为教学案例或全文可读；出版日期保留上游原值；原站排序可能变化，连续翻页需保持每页大小一致；源站未回显页码，已按总数校验返回条数。'}
