"""浙江科技报告公众检索与公开摘要；不读取联系方式或附件。"""
import release_runtime
import re
from urllib.parse import quote
import requests
_ROOT = 'https://kjbg.kjt.zj.gov.cn/rest/kjbg/wfKjbg/'
_BAD = re.compile('(?:https?://|www\\.|(?:token|session|api[_-]?key)\\s*=)', re.I)
_SEARCH_FIELDS = ('id', 'title', 'creator', 'creatOrorganization', 'uploadId', 'projectName')
_DETAIL_FIELDS = ('id', 'title', 'alternativeTitle', 'creator', 'creatOrorganization', 'prepareOrganization', 'publicScope', 'publicDate', 'createTime', 'uploadId', 'abstractCn', 'abstractEn', 'keywordsCn', 'keywordsEn', 'projectName', 'researchSubjectName', 'projectSubjectName', 'competentOrg', 'kjbgType', 'pagesCount', 'proposalDate', 'collectionDate', 'collectionNumber')

def _value(value):
    if value is None or (isinstance(value, (int, float)) and (not isinstance(value, bool))):
        return value
    return value if isinstance(value, str) and (not _BAD.search(value)) else None

def _pick(item, fields):
    if not isinstance(item, dict):
        raise ValueError('科技报告记录结构异常')
    out = {key: _value(item.get(key)) for key in fields}
    omitted = [key for key in fields if item.get(key) is not None and out[key] is None]
    if omitted:
        out['source_fields_omitted'] = omitted
    return out

def _post(endpoint, data):
    try:
        response = requests.post(_ROOT + endpoint, data=data, timeout=20)
        response.raise_for_status()
        payload = response.json()
    except (requests.RequestException, ValueError) as exc:
        raise RuntimeError('浙江科技报告请求失败或响应非 JSON') from exc
    if not isinstance(payload, dict) or payload.get('CODE') != '0' or (not isinstance(payload.get('RESULT'), dict)):
        raise RuntimeError('浙江科技报告返回错误或结构异常')
    return payload['RESULT']

def search(query, page=1):
    if not isinstance(query, str) or not query.strip() or len(query.strip()) > 20 or re.search('[\\x00-\\x1f]', query):
        raise ValueError('关键词须为 1–20 字单行文本')
    if isinstance(page, bool) or not isinstance(page, int) or (not 1 <= page <= 1000):
        raise ValueError('页码须为 1–1000')
    q = query.strip()
    result = _post('search', {'q': quote('All:' + q, safe=''), 'pageNo': str(page), 'orderBy': 'proposaldate desc', 'isAdvance': '1'})
    count, current, size, rows = (result.get(k) for k in ('count', 'pageNo', 'pageSize', 'list'))
    if any((isinstance(x, bool) or not isinstance(x, int) for x in (count, current, size))) or count < 0 or current != page or (size != 10) or (not isinstance(rows, list)) or (len(rows) > size):
        raise RuntimeError('浙江科技报告页码或题录结构异常')
    items = [_pick(x, _SEARCH_FIELDS) for x in rows]
    if any((not x['id'] or not x['title'] for x in items)):
        raise RuntimeError('科技报告缺少标识或题名')
    return {'source': '浙江省科技报告公众检索', 'query': q, 'page': page, 'page_size': size, 'total': count, 'items': items, 'note': '站方全部字段匹配，未回显关键词；公开题录不证明学校订购或全文权限。'}

def detail(report_id):
    if not isinstance(report_id, str) or not re.fullmatch('[0-9a-fA-F]{32}', report_id):
        raise ValueError('报告 ID 须为 32 位十六进制')
    source = _post('getFilde', {'id': report_id})
    if source.get('id') != report_id or not source.get('title'):
        raise ValueError('报告不存在或站方未回显相同 ID')
    record = _pick(source, _DETAIL_FIELDS)
    if not record.get('title'):
        raise RuntimeError('报告题名异常')
    return {'source': '浙江省科技报告公开详情', 'record': record, 'note': '公开基本信息与摘要；不含联系方式、附件或全文，机构订购未验证。'}
