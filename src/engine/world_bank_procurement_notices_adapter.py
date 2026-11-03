"""World Bank project procurement notices public search."""
import release_runtime
import requests
URL = 'https://search.worldbank.org/api/v2/procnotices'
CATALOG = 'https://datacatalog.worldbank.org/search/dataset/0037795/world-bank-procurement-notices'
NOTE = '世界银行资助项目采购公告，包含招标、意向征询及合同授予等多类记录；并非各国全部采购。关键词为全文搜索，不等同于国家筛选；状态、公告日期、截止日期、金额和字段原样保留。当前结果不是历史时点快照；申请前以项目方原始公告及最新修订为准。'

def notices(keyword='', notice_id='', rows=20, offset=0, session=None):
    if not isinstance(keyword, str) or len(keyword) > 200:
        raise ValueError('关键词长度不可超过 200 字符')
    if not isinstance(notice_id, str) or len(notice_id) > 80:
        raise ValueError('公告编号格式不正确')
    if isinstance(rows, bool) or not isinstance(rows, int) or (not 1 <= rows <= 100):
        raise ValueError('每页数量须为 1 至 100')
    if isinstance(offset, bool) or not isinstance(offset, int) or offset < 0:
        raise ValueError('起始记录须为非负整数')
    params = {'format': 'json', 'rows': rows, 'os': offset}
    if keyword.strip():
        params['qterm'] = keyword.strip()
    if notice_id.strip():
        params['id'] = notice_id.strip()
    r = (session or requests).get(URL, params=params, headers={'Accept': 'application/json', 'User-Agent': 'PersonalResearchToolkit/1.0'}, timeout=35)
    r.raise_for_status()
    try:
        data = r.json()
    except ValueError as exc:
        raise ValueError('世界银行接口未返回 JSON') from exc
    if not isinstance(data, dict) or not isinstance(data.get('procnotices'), list) or 'total' not in data:
        raise ValueError('世界银行公告数据格式异常')
    return {'source': 'World Bank Procurement Notices', 'source_url': r.url, 'catalog': CATALOG, 'license': 'CC BY 4.0 (see catalog)', 'note': NOTE, 'data': data}
