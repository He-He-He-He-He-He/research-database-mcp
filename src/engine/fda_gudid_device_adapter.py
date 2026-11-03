"""Public openFDA GUDID search and NLM AccessGUDID exact device lookup."""
import release_runtime
import re
import requests
FDA = 'https://api.fda.gov/device/udi.json'
NLM = 'https://accessgudid.nlm.nih.gov/api/v2/devices/lookup.json'
NOTE = '美国 GUDID 医疗器械标识信息由标签商提交并经 openFDA 或美国国家医学图书馆公开；登记或列出不表示 FDA 批准、安全、有效或适合个体使用；不能依据结果作医疗决定。记录可能修订、撤销或停产，原始分销状态、版本日期及标识类型须核对；当前结果非历史快照。无密钥 openFDA 有调用限额，缺失信息不代表否。'

def search(field, term, limit=10, skip=0, session=None):
    if field not in ('brand_name', 'company_name'):
        raise ValueError('字段须为 brand_name 或 company_name')
    if not isinstance(term, str) or not term.strip() or len(term) > 120 or (not re.fullmatch("[\\w .,'&+()/\\-]+", term, flags=re.UNICODE)):
        raise ValueError('关键词含不支持的查询符号或长度不正确')
    if isinstance(limit, bool) or not isinstance(limit, int) or (not 1 <= limit <= 100):
        raise ValueError('每页须为 1 至 100 条')
    if isinstance(skip, bool) or not isinstance(skip, int) or (not 0 <= skip <= 25000):
        raise ValueError('跳过条数须为 0 至 25000')
    p = {'search': field + ':"' + term.strip() + '"', 'limit': limit, 'skip': skip}
    r = (session or requests).get(FDA, params=p, timeout=30, headers={'Accept': 'application/json', 'User-Agent': 'PersonalResearchToolkit/1.0'})
    if r.status_code == 404:
        try:
            d = r.json()
        except ValueError:
            d = {}
        if d.get('error', {}).get('code') == 'NOT_FOUND':
            return {'source': 'openFDA Device UDI', 'source_url': r.url, 'note': NOTE, 'data': {'results': [], 'upstream': d}}
    r.raise_for_status()
    d = r.json()
    if not isinstance(d, dict) or not isinstance(d.get('results'), list) or (not isinstance(d.get('meta'), dict)):
        raise ValueError('openFDA 响应异常')
    return {'source': 'openFDA Device UDI', 'source_url': r.url, 'documentation': 'https://open.fda.gov/apis/device/udi/', 'note': NOTE, 'data': d}

def lookup(di, session=None):
    if not isinstance(di, str) or not re.fullmatch('[A-Za-z0-9.\\-]{1,80}', di):
        raise ValueError('设备标识 DI 格式无效；保留前导零')
    r = (session or requests).get(NLM, params={'di': di}, timeout=30, headers={'Accept': 'application/json', 'User-Agent': 'PersonalResearchToolkit/1.0'})
    r.raise_for_status()
    d = r.json()
    if not isinstance(d, dict) or not isinstance(d.get('gudid'), dict) or (not isinstance(d['gudid'].get('device'), dict)):
        raise ValueError('AccessGUDID 记录不存在或格式异常')
    return {'source': 'U.S. National Library of Medicine AccessGUDID', 'source_url': r.url, 'documentation': 'https://accessgudid.nlm.nih.gov/resources/developers/device_lookup_api', 'note': NOTE, 'data': d}
