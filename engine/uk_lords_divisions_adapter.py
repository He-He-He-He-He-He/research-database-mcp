"""UK Parliament Lords Votes API, search and official division details."""
import release_runtime
import datetime, json
import requests
BASE = 'https://lordsvotes-api.parliament.uk/data/Divisions/'
DOCS = 'https://lordsvotes-api.parliament.uk/index.html'
NOTE = '英国上议院正式分组表决，不是下议院投票。议员名单、计票员、赞成反对及官方 authoritative 和 member 分项按原始字段保留，不得将不同计数重复相加。未出现于名单不等于弃权；单次投票不代表法律已经生效。官方记录可能更新，当前查询不构成历史时点快照。'

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
        raise ValueError('上议院接口未返回 JSON') from exc
    return {'source': 'UK Parliament Lords Votes API', 'source_url': url, 'documentation': DOCS, 'note': NOTE, 'data': data}

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
    p = {'StartDate': start, 'EndDate': end, 'take': take, 'skip': skip}
    if keyword.strip():
        p['SearchTerm'] = keyword.strip()
    result = _fetch('search', p, session)
    if not isinstance(result['data'], list):
        raise ValueError('表决检索数据格式异常')
    result['page_note'] = '仅显示所请求页；总数端点未调用，当前页不代表全部。'
    return result

def detail(division_id, session=None):
    if isinstance(division_id, bool) or not isinstance(division_id, int) or division_id < 1:
        raise ValueError('division ID 须为正整数')
    result = _fetch(str(division_id), session=session)
    if not isinstance(result['data'], dict) or result['data'].get('divisionId') != division_id:
        raise ValueError('表决详情缺失或编号不符')
    return result
