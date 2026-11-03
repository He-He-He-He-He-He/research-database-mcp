"""AI 技术经纪人学校 IP 会话：推荐专家列表。"""
import release_runtime
import re
import requests
BASE = 'https://www.cstservice.cn'
FIELDS = ('ID', 'NAME', 'ORG', 'AORG', 'TITLE', 'DIRECTION', 'KEYWORDS', 'TAGS')

def recommend(query, offset=0, limit=5, session=None):
    if not isinstance(query, str) or not 1 <= len(query.strip()) <= 80 or re.search('[\\x00-\\x1f]', query):
        raise ValueError('检索词须为 1–80 字的单行文本')
    if type(offset) is not int or not 0 <= offset <= 999:
        raise ValueError('offset 须为 0–999')
    if type(limit) is not int or not 1 <= limit <= 20:
        raise ValueError('limit 须为 1–20')
    s = session or requests.Session()
    try:
        r = s.get(BASE + '/apis/sys/autoLogin', timeout=25, allow_redirects=False)
        if r.status_code != 200:
            raise RuntimeError('机构认证服务不可用')
        j = r.json()
        obj = j.get('result')
        user = obj.get('userInfo') if isinstance(obj, dict) else None
        if j.get('code') != 200 or not isinstance(user, dict) or user.get('realname') != '浙江大学' or (user.get('orgCodeTxt') != '浙江大学') or (not isinstance(obj.get('token'), str)) or (not obj['token']):
            raise RuntimeError('未确认浙江大学机构身份')
        expiry = user.get('expirationDate')
        r = s.get(BASE + '/apis/talent/findExpert', params={'key': query.strip(), 'from': offset, 'size': limit}, headers={'X-Access-Token': obj['token']}, timeout=45, allow_redirects=False)
        if r.status_code != 200:
            raise RuntimeError('专家查询服务不可用')
        j = r.json()
        d = j.get('data')
        if j.get('code') != 200 or not isinstance(d, dict) or type(d.get('total')) is not int or (d['total'] < 0):
            raise RuntimeError('专家查询响应未确认')
        rows = d.get('expertsRecommend', [])
        if not isinstance(rows, list) or len(rows) > limit or any((not isinstance(x, dict) or not x.get('NAME') for x in rows)):
            raise RuntimeError('专家结果格式异常')

        def safe(v):
            if v is None or type(v) in (str, int, float):
                return v
            if isinstance(v, list) and all((x is None or type(x) in (str, int, float) for x in v)):
                return v
            return None
        items = [{k: safe(x[k]) for k in FIELDS if k in x} for x in rows]
        return {'source': 'AI 技术经纪人专家推荐', 'institution': '浙江大学', 'institution_expiration_raw': expiry, 'library_trial_until_raw': '2026-12-31', 'library_info': 'https://libdb.zju.edu.cn/s/lib/libtb/show/2129', 'query': query.strip(), 'offset': offset, 'limit': limit, 'total': d['total'], 'items': items, 'note': '馆方公告试用截止日与站方账户到期日口径未核，均以原值保留。平台推荐结果及署名机构、职称和方向未经独立核实；可能同名或机构变化。总数和排序由站方给出，不等于完整专家名录；仅元数据，不代表论文或成果全文权限。'}
    except (requests.RequestException, ValueError) as e:
        if isinstance(e, ValueError) and (not isinstance(e, requests.RequestException)):
            raise RuntimeError('上游响应无法解析') from None
        raise RuntimeError('机构服务连接失败') from None
