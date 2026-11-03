"""UK Parliament Commons Votes API, search and official division details."""
import release_runtime
import datetime, json
import requests
BASE = 'https://commonsvotes-api.parliament.uk/data/'
DOCS = 'https://commonsvotes-api.parliament.uk/swagger/ui/index'
NOTE = '英国下议院正式分组表决记录，标题、投票日期、计票员及赞成反对记录均按官方原值返回。一项法案可能经历多次表决；某次表决结果不代表法案已全部通过或已生效。未出现在赞成或反对名单的人不应直接认定为弃权；表决覆盖与议员资格请核对官方原始记录。历史记录可能更正，PublicationUpdated 与表决日期不同；查询当前数据库不是历史快照。'

def _fetch(path, params=None, session=None):
    with (session or requests).get(BASE + path, params=params, headers={'Accept': 'application/json', 'User-Agent': 'PersonalResearchToolkit/1.0'}, timeout=35, stream=True) as r:
        r.raise_for_status()
        body = bytearray()
        for c in r.iter_content(65536):
            body.extend(c)
            if len(body) > 12 * 1024 * 1024:
                raise ValueError('响应超过 12 MiB，请缩小每页数量')
        url = r.url
    try:
        data = json.loads(body)
    except ValueError as exc:
        raise ValueError('下议院接口未返回 JSON') from exc
    return {'source': 'UK Parliament Commons Votes API', 'source_url': url, 'documentation': DOCS, 'note': NOTE, 'data': data}

def search(start, end, keyword='', take=10, skip=0, session=None):
    try:
        a = datetime.date.fromisoformat(start)
        b = datetime.date.fromisoformat(end)
    except (ValueError, TypeError):
        raise ValueError('起止日期须为 YYYY-MM-DD') from None
    if a > b:
        raise ValueError('起始日期晚于结束日期')
    if not isinstance(keyword, str) or len(keyword) > 200:
        raise ValueError('关键词最多 200 字符')
    if isinstance(take, bool) or not isinstance(take, int) or (not 1 <= take <= 100):
        raise ValueError('每页数量应为 1 至 100')
    if isinstance(skip, bool) or not isinstance(skip, int) or skip < 0:
        raise ValueError('跳过条数须为非负整数')
    p = {'queryParameters.startDate': start, 'queryParameters.endDate': end, 'queryParameters.take': take, 'queryParameters.skip': skip}
    if keyword.strip():
        p['queryParameters.searchTerm'] = keyword.strip()
    result = _fetch('divisions.json/search', p, session)
    if not isinstance(result['data'], list):
        raise ValueError('表决检索数据格式异常')
    result['page_note'] = '仅显示所请求页；数据接口另提供 searchTotalResults，当前未查询总数。'
    return result

def detail(division_id, session=None):
    if isinstance(division_id, bool) or not isinstance(division_id, int) or division_id < 1:
        raise ValueError('division ID 须为正整数')
    result = _fetch(f'division/{division_id}.json', session=session)
    if not isinstance(result['data'], dict) or result['data'].get('DivisionId') != division_id:
        raise ValueError('表决详情缺失或编号不符')
    return result
