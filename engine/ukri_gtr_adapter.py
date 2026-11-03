"""UKRI Gateway to Research public project search and project detail."""
import release_runtime
from urllib.parse import urlencode
import requests
BASE = 'https://gtr.ukri.org/api'
HEADERS = {'Accept': 'application/json', 'User-Agent': 'PersonalResearchToolkit/1.0'}

def _get(path, params, session=None):
    response = (session or requests).get(BASE + path, params=params, headers=HEADERS, timeout=25)
    response.raise_for_status()
    try:
        payload = response.json()
    except ValueError as exc:
        raise ValueError('UKRI 返回的不是 JSON') from exc
    if not isinstance(payload, dict):
        raise ValueError('UKRI 返回格式异常')
    return payload

def search_projects(term, page=1, fetch_size=25, session=None):
    if not isinstance(term, str) or not term.strip() or len(term) > 200:
        raise ValueError('检索词不能为空且最多 200 字符')
    if isinstance(page, bool) or not isinstance(page, int) or page < 1:
        raise ValueError('页码必须是正整数')
    if isinstance(fetch_size, bool) or not isinstance(fetch_size, int) or (not 25 <= fetch_size <= 100):
        raise ValueError('每页大小应为 25 至 100')
    params = {'term': term.strip(), 'page': page, 'fetchSize': fetch_size}
    payload = _get('/search/project', params, session)
    bean = payload.get('facetedSearchResultBean')
    if not isinstance(bean, dict) or not isinstance(bean.get('results'), list):
        raise ValueError('UKRI 项目检索结果缺失')
    return {'source': 'UK Research and Innovation Gateway to Research', 'source_url': BASE + '/search/project?' + urlencode(params), 'documentation': 'https://gtr.ukri.org/resources/gtrapi-search-api.html', 'note': '公开资助项目数据库；筛选、覆盖、周期、遗漏和项目转移重复金额等限制请参考 UKRI 官方指南。研究资金字段原样保留，不可简单相加。', 'data': payload}

def project_detail(reference, session=None):
    if not isinstance(reference, str) or not reference.strip() or len(reference) > 150:
        raise ValueError('项目编号不能为空且最多 150 字符')
    params = {'ref': reference.strip()}
    payload = _get('/projects', params, session)
    if not isinstance(payload.get('projectOverview'), dict):
        raise ValueError('UKRI 项目详情缺失或项目编号无效')
    return {'source': 'UK Research and Innovation Gateway to Research', 'source_url': BASE + '/projects?' + urlencode(params), 'documentation': 'https://gtr.ukri.org/resources/gtrapi-project-api.html', 'note': '金额、日期及项目上下级关系保留原值；转移项目可能造成金额重复统计。', 'data': payload}
