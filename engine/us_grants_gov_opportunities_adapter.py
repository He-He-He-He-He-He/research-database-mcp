"""Grants.gov official, unauthenticated public opportunity search and detail."""
import release_runtime
import requests
BASE = 'https://api.grants.gov/v1/api/'
DOCS = 'https://www.grants.gov/api/api-guide'
NOTE = '美国联邦资助机会公告，不是已授予项目或实际拨款记录；以资助机构完整公告与资格条件为准。状态、日期和金额保留源值；posted 不必然意味着当前可以申请，可能有过期或未填写截止日期。当前检索结果不是历史时点快照；请核实详情及更新日期。'

def _post(endpoint, body, session=None):
    r = (session or requests).post(BASE + endpoint, json=body, headers={'Accept': 'application/json', 'User-Agent': 'PersonalResearchToolkit/1.0'}, timeout=30)
    r.raise_for_status()
    try:
        payload = r.json()
    except ValueError as exc:
        raise ValueError('Grants.gov 返回内容不是 JSON') from exc
    if not isinstance(payload, dict) or payload.get('errorcode') != 0 or (not isinstance(payload.get('data'), dict)):
        raise ValueError('Grants.gov 接口返回错误或数据格式异常')
    return payload['data']

def search_opportunities(keyword, status='posted', rows=20, start=0, session=None):
    if not isinstance(keyword, str) or not keyword.strip() or len(keyword) > 200:
        raise ValueError('关键词应为 1 至 200 字符')
    if status not in ('posted', 'forecasted', 'closed', 'archived', 'all'):
        raise ValueError('状态必须为 posted、forecasted、closed、archived 或 all')
    if isinstance(rows, bool) or not isinstance(rows, int) or (not 1 <= rows <= 100):
        raise ValueError('每页应为 1 至 100 条')
    if isinstance(start, bool) or not isinstance(start, int) or start < 0:
        raise ValueError('起始记录须为非负整数')
    statuses = 'forecasted|posted|closed|archived' if status == 'all' else status
    body = {'keyword': keyword.strip(), 'oppStatuses': statuses, 'rows': rows, 'startRecordNum': start}
    data = _post('search2', body, session)
    if not isinstance(data.get('oppHits'), list) or not isinstance(data.get('hitCount'), int):
        raise ValueError('Grants.gov 搜索结果缺少必要字段')
    return {'source': 'Grants.gov, U.S. Department of Health and Human Services', 'source_url': BASE + 'search2', 'documentation': DOCS, 'request': body, 'note': NOTE, 'data': data}

def opportunity_detail(opportunity_id, session=None):
    if isinstance(opportunity_id, bool) or not isinstance(opportunity_id, int) or opportunity_id <= 0:
        raise ValueError('机会编号须为正整数')
    body = {'opportunityId': opportunity_id}
    data = _post('fetchOpportunity', body, session)
    if not data.get('id') or not data.get('opportunityTitle'):
        raise ValueError('Grants.gov 详情缺少编号或标题')
    return {'source': 'Grants.gov, U.S. Department of Health and Human Services', 'source_url': BASE + 'fetchOpportunity', 'documentation': 'https://www.grants.gov/api/common/fetchopportunity', 'request': body, 'note': NOTE, 'data': data}
