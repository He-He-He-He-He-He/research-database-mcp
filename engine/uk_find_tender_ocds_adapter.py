"""UK Find a Tender official OCDS release packages."""
import release_runtime
import datetime, json, re
import requests
URL = 'https://www.find-tender.service.gov.uk/api/1.0/ocdsReleasePackages'
DOCS = 'https://www.find-tender.service.gov.uk/apidocumentation/1.0/GET-ocdsReleasePackages'
NOTE = 'Find a Tender 采购过程公告的 OCDS releases，不代表全部英国采购；同一采购可能有多个阶段或修订。updatedFrom 和 updatedTo 是记录更新时间，不等同首次发布时间或提交截止时间；历史日期筛选不是历史时点快照。规划、招标、授予不等同已付款；须检查每条公告阶段、状态、币种、资格、截止时间与后续修订。分页请使用官方 links.next 的 cursor；单页不能当作全部结果。'

def releases(start='', end='', stage='', limit=20, cursor='', identifier='', session=None):
    for value in (start, end):
        if value:
            try:
                if not re.fullmatch('\\d{4}-\\d{2}-\\d{2}T\\d{2}:\\d{2}:\\d{2}', value):
                    raise ValueError
                datetime.datetime.strptime(value, '%Y-%m-%dT%H:%M:%S')
            except (TypeError, ValueError):
                raise ValueError('时间须为 YYYY-MM-DDTHH:MM:SS') from None
    if start and end and (start > end):
        raise ValueError('结束时间不得早于开始时间')
    if stage not in ('', 'planning', 'tender', 'award'):
        raise ValueError('阶段须为 planning、tender 或 award')
    if isinstance(limit, bool) or not isinstance(limit, int) or (not 1 <= limit <= 100):
        raise ValueError('每页数量须为 1 至 100')
    if not isinstance(cursor, str) or len(cursor) > 300 or (cursor and (not re.fullmatch('[A-Za-z0-9=]+', cursor))):
        raise ValueError('无效游标')
    if not isinstance(identifier, str) or (identifier and (not re.fullmatch('(?:\\d{6}-\\d{4}|ocds-h6vhtk-[0-9a-f]{6})', identifier))):
        raise ValueError('公告或采购过程编号格式错误')
    params = {'limit': limit}
    for key, value in [('updatedFrom', start), ('updatedTo', end), ('stages', stage), ('cursor', cursor)]:
        if value:
            params[key] = value
    u = URL + ('/' + identifier if identifier else '')
    with (session or requests).get(u, params=params, headers={'Accept': 'application/json', 'User-Agent': 'PersonalResearchToolkit/1.0'}, timeout=35, stream=True) as r:
        r.raise_for_status()
        content = bytearray()
        for chunk in r.iter_content(65536):
            content.extend(chunk)
            if len(content) > 12 * 1024 * 1024:
                raise ValueError('响应超过 12 MiB，请缩小分页数量')
        source_url = r.url
    try:
        data = json.loads(content)
    except ValueError as exc:
        raise ValueError('英国 Find a Tender 未返回 JSON') from exc
    if not isinstance(data, dict) or not isinstance(data.get('releases'), list):
        raise ValueError('公告数据格式异常')
    return {'source': 'UK Cabinet Office Find a Tender', 'source_url': source_url, 'documentation': DOCS, 'note': NOTE, 'data': data}
